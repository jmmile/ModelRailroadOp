from modelrailroadops.services.industry_service import IndustryService
from modelrailroadops.services.industry_track_service import IndustryTrackService


print("Getting industries...")

industries = IndustryService.get_all()

if not industries:
    print("No industries found. Add an industry first.")
    exit()

for industry in industries:
    print(industry.id, industry.name)

industry_id = industries[0].id


print("\nAdding test industry track...")

track = IndustryTrackService.add(
    industry_id,
    "Track 1",
    3
)

print(
    "Created:",
    track.id,
    track.name,
    track.spots
)


print("\nGetting all industry tracks...")

tracks = IndustryTrackService.get_all()

for track in tracks:
    print(
        track.id,
        track.name,
        track.spots,
        track.industry_id
    )


print("\nUpdating track...")

updated = IndustryTrackService.update(
    track.id,
    name="Track 1 Updated",
    spots=4
)

print(
    "Updated:",
    updated.id,
    updated.name,
    updated.spots
)


print("\nDeleting track...")

deleted = IndustryTrackService.delete(track.id)

print("Deleted:", deleted)