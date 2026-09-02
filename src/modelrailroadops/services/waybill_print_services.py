from PySide6.QtCore import QRectF, QSizeF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter

from modelrailroadops.ui.waybills.waybill_form import (
    WaybillFormRenderer,
)


class WaybillPrintService:
    """
    Handles printing Model Railroad Operations waybills.

    Waybill forms are printed at their actual logical size:

        3.75 inches wide
        4.00 inches high

    Up to four waybills are placed on each page.

    The existing WaybillFormRenderer is used for the actual
    form drawing so that the printed form matches the preview.
    """

    FORMS_PER_PAGE = 4

    FORM_WIDTH_INCHES = (
        WaybillFormRenderer.WIDTH_INCHES
    )

    FORM_HEIGHT_INCHES = (
        WaybillFormRenderer.HEIGHT_INCHES
    )

    @staticmethod
    def inches_to_printer_units(
        inches,
        dpi,
    ):
        """
        Convert inches to printer pixels.
        """

        return int(
            round(
                inches * dpi
            )
        )

    @classmethod
    def print_waybills(
        cls,
        waybills,
        parent=None,
    ):
        """
        Print the supplied waybills.

        Returns True when printing is successfully
        completed, or False when printing is cancelled
        or cannot be started.
        """

        if not waybills:
            return False

        printer = QPrinter(
            QPrinter.HighResolution
        )

        #
        # Open the normal Qt printer dialog.
        #

        print_dialog = QPrintDialog(
            printer,
            parent,
        )

        result = print_dialog.exec()

        if result != QPrintDialog.DialogCode.Accepted:
            return False

        #
        # Determine the printer's actual DPI.
        #

        dpi_x = printer.logicalDpiX()
        dpi_y = printer.logicalDpiY()

        if dpi_x <= 0:
            dpi_x = printer.resolution()

        if dpi_y <= 0:
            dpi_y = printer.resolution()

        #
        # Convert the physical waybill size into
        # printer units.
        #

        form_width = (
            cls.inches_to_printer_units(
                cls.FORM_WIDTH_INCHES,
                dpi_x,
            )
        )

        form_height = (
            cls.inches_to_printer_units(
                cls.FORM_HEIGHT_INCHES,
                dpi_y,
            )
        )

        #
        # Obtain the printable page rectangle.
        #
        # This is expressed in printer coordinates.
        #

        page_rect = printer.pageRect(
            QPrinter.Unit.DevicePixel
        )

        page_width = (
            page_rect.width()
        )

        page_height = (
            page_rect.height()
        )

        if page_width <= 0 or page_height <= 0:
            return False

        #
        # Determine how much room is available for
        # four 3.75" x 4" forms.
        #
        # The forms are arranged vertically when the
        # page allows it. Otherwise they are arranged
        # horizontally/vertically according to the
        # available printable area.
        #

        vertical_required = (
            form_height
            * cls.FORMS_PER_PAGE
        )

        horizontal_required = (
            form_width
            * cls.FORMS_PER_PAGE
        )

        if vertical_required <= page_height:
            columns = 1
            rows = cls.FORMS_PER_PAGE

        elif horizontal_required <= page_width:
            columns = cls.FORMS_PER_PAGE
            rows = 1

        else:
            #
            # Standard letter paper normally has enough
            # room for two 3.75" wide forms and two 4"
            # high forms, so this is the normal layout.
            #

            columns = 2
            rows = 2

        #
        # For a standard portrait page, two columns by
        # two rows is preferred when the four forms fit.
        #

        if (
            form_width * 2 <= page_width
            and form_height * 2 <= page_height
        ):
            columns = 2
            rows = 2

        forms_per_page = (
            columns * rows
        )

        #
        # Calculate the total occupied area.
        #

        total_width = (
            form_width * columns
        )

        total_height = (
            form_height * rows
        )

        #
        # Center the group of forms inside the
        # printable page area.
        #

        start_x = (
            page_rect.x()
            + (
                page_width
                - total_width
            ) / 2
        )

        start_y = (
            page_rect.y()
            + (
                page_height
                - total_height
            ) / 2
        )

        #
        # Create the painter.
        #

        painter = QPainter()

        if not painter.begin(printer):
            return False

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        painter.setRenderHint(
            QPainter.RenderHint.TextAntialiasing,
            True,
        )

        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform,
            True,
        )

        try:
            for index, waybill in enumerate(
                waybills
            ):

                page_position = (
                    index % forms_per_page
                )

                #
                # Start a new page after the first
                # group of forms.
                #

                if (
                    index > 0
                    and page_position == 0
                ):
                    if not printer.newPage():
                        return False

                column = (
                    page_position % columns
                )

                row = (
                    page_position // columns
                )

                form_x = (
                    start_x
                    + (
                        column
                        * form_width
                    )
                )

                form_y = (
                    start_y
                    + (
                        row
                        * form_height
                    )
                )

                form_rect = QRectF(
                    form_x,
                    form_y,
                    form_width,
                    form_height,
                )

                #
                # Draw the exact same form used
                # by the preview dialog.
                #

                renderer = (
                    WaybillFormRenderer(
                        waybill
                    )
                )

                renderer.draw(
                    painter,
                    form_rect,
                )

        finally:
            painter.end()

        return True