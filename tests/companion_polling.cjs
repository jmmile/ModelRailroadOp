// No browser/test dependencies: run the actual inline script in a controlled VM.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
    if (!elements.has(id)) elements.set(id, {
        value: '', disabled: false, style: {}, innerHTML: '', textContent: '',
        classList: {visible: false, contains() {return this.visible;},
            add() {this.visible = true;}, remove() {this.visible = false;}},
        addEventListener() {}, appendChild() {}, focus() {}, setAttribute() {},
    });
    return elements.get(id);
}
const timers = [];
const context = vm.createContext({
    document: {hidden: false, body: element('body'), getElementById: element,
        createElement: () => element(Symbol()), addEventListener() {}},
    setInterval: (callback, delay) => timers.push({callback, delay}),
    fetch: async () => ({ok: true, json: async () => ({authenticated: false})}),
    console,
});
const script = fs.readFileSync(process.argv[2], 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
vm.runInContext(script, context);
async function run() {
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(timers.length, 1);
    assert.equal(timers[0].delay, 4000);
    await vm.runInContext(`(async () => {
        let calls = 0;
        let rendered = [];
        let pending = [];
        renderMoves = moves => rendered.push(moves);
        fetch = (url, options) => {
            if (options.credentials !== "same-origin") throw Error("Missing credentials");
            calls++;
            return new Promise(resolve => pending.push(resolve));
        };
        const check = (value, message) => {if (!value) throw Error(message);};
        const reply = async data => {
            pending.shift()({ok: true, json: async () => data});
            await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
        };
        companionScreen.style.display = "block";
        await refreshMovesAutomatically();
        check(calls === 0, "Must not poll without selection");
        sessionSelect.value = "1"; trainSelect.value = "2";
        trainSelect.disabled = false;
        let first = refreshMovesAutomatically();
        await refreshMovesAutomatically();
        check(calls === 1, "Overlapping poll");
        await reply([{status: "COMPLETED"}]); await first;
        check(rendered.length === 1, "Completed move not rendered");
        for (const modal of [moveConfirmationModal, waybillModal]) {
            modal.classList.add("visible");
            await refreshMovesAutomatically();
            check(calls === 1, "Polled during dialog");
            modal.classList.remove("visible");
            first = refreshMovesAutomatically();
            modal.classList.add("visible");
            await reply([]); await first;
            check(rendered.length === 1, "Applied response during dialog");
            check(modal.classList.contains("visible"), "Closed dialog");
            modal.classList.remove("visible");
            calls = 1;
        }
        first = refreshMovesAutomatically();
        trainSelect.value = "3";
        const manual = loadMoves("1", "3");
        check(pending.length === 2, "Manual selection blocked by polling");
        await reply(["old"]); await first;
        check(rendered.length === 1, "Stale train rendered");
        await reply(["new"]); await manual;
        check(rendered[1][0] === "new", "New train missing");
        first = refreshMovesAutomatically();
        sessionSelect.value = "9";
        await reply(["old session"]); await first;
        check(rendered.length === 2, "Stale session rendered");
        completingMoves++;
        const before = calls;
        await refreshMovesAutomatically();
        check(calls === before, "Polled during completion");
        completingMoves--;
        first = refreshMovesAutomatically();
        await reply(["resumed"]); await first;
        check(rendered[2][0] === "resumed", "Polling did not resume");
        first = refreshMovesAutomatically();
        pending.shift()({ok: false, status: 503}); await first;
        check(activeMoveRequests === 0, "Failed request left polling blocked");
        first = refreshMovesAutomatically();
        pending.shift()({ok: false, status: 401}); await first;
        check(companionScreen.style.display === "none", "401 did not unpair");
        const unpairedCalls = calls;
        await refreshMovesAutomatically();
        check(calls === unpairedCalls, "Polled while unpaired");
    })()`, context);
    console.log('Polling, overlap, stale responses, dialogs, completion, retry and authentication passed');
}
run().catch(error => {console.error(error); process.exitCode = 1;});
