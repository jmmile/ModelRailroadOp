from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QImage, QPainter, QPen, QPixmap


class WaybillFormRenderer:
    """
    Draws the Model Railroad Operations waybill form.

    The logical form size is exactly:

        3.75 inches wide
        4.00 inches high

    The renderer can draw the form on a screen pixmap or directly
    onto a printer.

    Font sizes are specified in points rather than being calculated
    from printer device pixels. This keeps text physically
    consistent at different printer resolutions.
    """

    WIDTH_INCHES = 3.75
    HEIGHT_INCHES = 4.00

    IMAGE_DIRECTORY = (
        "data"
        "/"
        "Car_Images"
    )

    def __init__(
        self,
        waybill,
    ):

        self.waybill = waybill

    # ------------------------------------------------------------------
    # Unit conversion
    # ------------------------------------------------------------------

    @staticmethod
    def inches_to_pixels(
        inches,
        dpi,
    ):

        return int(
            round(
                inches * dpi
            )
        )

    @staticmethod
    def points_to_pixels(
        points,
        dpi,
    ):

        return (
            float(points)
            * float(dpi)
            / 72.0
        )

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_text(
        value,
    ):

        if value is None:
            return ""

        return str(
            value
        )

    @staticmethod
    def _car_text(
        waybill,
    ):

        if waybill.car is None:
            return "Unknown"

        reporting_mark = (
            waybill.car.reporting_mark
            or ""
        )

        number = (
            waybill.car.number
            or ""
        )

        return (
            f"{reporting_mark} {number}"
        ).strip()

    @staticmethod
    def _car_type(
        waybill,
    ):

        if waybill.car is None:
            return ""

        return (
            waybill.car.car_type
            or ""
        )

    @staticmethod
    def _car_status(
        waybill,
    ):

        if waybill.car is None:
            return ""

        return (
            waybill.car.status
            or ""
        )

    @staticmethod
    def _car_type_and_status(waybill):
        values = [
            WaybillFormRenderer._car_type(waybill),
            WaybillFormRenderer._car_status(waybill),
        ]
        return " / ".join(value for value in values if value)

    @staticmethod
    def _load_state_text(waybill):
        if waybill.load_state == "LOADED":
            return "Loaded"
        if waybill.load_state == "EMPTY":
            return "Empty"
        return "Not specified"

    @staticmethod
    def _weight_text(waybill):
        if waybill.gross_weight_lbs is None:
            return "Not calculated"

        return (
            f"{waybill.gross_weight_lbs:,} lb\n"
            f"{waybill.tonnage:,.1f} short tons"
        )

    @staticmethod
    def _origin_text(
        waybill,
    ):

        lines = []

        location = (
            waybill.origin_location
            or ""
        )

        if location:
            lines.append(
                location
            )

        if waybill.origin_operating_location is not None:

            operating_location_name = (
                waybill.origin_operating_location.name
                or ""
            )

            if operating_location_name and operating_location_name not in lines:
                lines.append(operating_location_name)

        if waybill.origin_operating_track is not None:

            operating_track_name = (
                waybill.origin_operating_track.name
                or ""
            )

            if operating_track_name:
                lines.append(operating_track_name)

        if waybill.origin_industry is not None:

            industry_name = (
                waybill.origin_industry.name
                or ""
            )

            if (
                industry_name
                and industry_name not in lines
            ):
                lines.append(
                    industry_name
                )

        if waybill.origin_track is not None:

            track_name = (
                waybill.origin_track.name
                or ""
            )

            if track_name and track_name not in lines:
                lines.append(
                    track_name
                )

        if waybill.origin_spot is not None:

            lines.append(
                f"Spot "
                f"{waybill.origin_spot.spot_number}"
            )

        return "\n".join(
            line
            for line in lines
            if line
        )

    @staticmethod
    def _destination_text(
        waybill,
    ):

        lines = []

        if waybill.destination_operating_location is not None:

            location_name = (
                waybill.destination_operating_location.name
                or ""
            )

            if location_name:
                lines.append(location_name)

        if waybill.destination_operating_track is not None:

            operating_track_name = (
                waybill.destination_operating_track.name
                or ""
            )

            if operating_track_name:
                lines.append(operating_track_name)

        if waybill.destination_industry is not None:

            industry_name = (
                waybill.destination_industry.name
                or ""
            )

            if industry_name and industry_name not in lines:
                lines.append(
                    industry_name
                )

        if waybill.destination_track is not None:

            track_name = (
                waybill.destination_track.name
                or ""
            )

            if track_name and track_name not in lines:
                lines.append(
                    track_name
                )

        if waybill.destination_spot is not None:

            lines.append(
                f"Spot "
                f"{waybill.destination_spot.spot_number}"
            )

        return "\n".join(
            line
            for line in lines
            if line
        )

    @staticmethod
    def _created_text(
        waybill,
    ):

        if waybill.created_at is None:
            return ""

        return waybill.created_at.strftime(
            "%m/%d/%Y"
        )

    # ------------------------------------------------------------------
    # Car image
    # ------------------------------------------------------------------

    @staticmethod
    def _project_root():
        """
        Return the Model RailroadOps project root.

        This file is located at:

            src/modelrailroadops/ui/waybills/waybill_form.py

        so the project root is four levels above this file.
        """

        return (
            Path(__file__)
            .resolve()
            .parents[4]
        )

    def _car_image_path(
        self,
    ):
        """
        Find the PNG image for the assigned car.

        Supported filename formats include:

            UP_123456.png
            UP 123456.png
            UP123456.png

        Filename matching is case-insensitive.
        """

        if self.waybill.car is None:
            return None

        return self.find_car_image_path(
            self.waybill.car.reporting_mark,
            self.waybill.car.number,
        )

    @classmethod
    def find_car_image_path(
        cls,
        reporting_mark,
        number,
    ):
        """Find a car PNG from its reporting mark and number."""

        reporting_mark = (
            reporting_mark
            or ""
        ).strip()

        number = (
            number
            or ""
        ).strip()

        if not reporting_mark or not number:
            return None

        image_directory = (
            cls._project_root()
            / cls.IMAGE_DIRECTORY
        )

        if not image_directory.is_dir():
            return None

        possible_names = [
            f"{reporting_mark}_{number}.png",
            f"{reporting_mark} {number}.png",
            f"{reporting_mark}{number}.png",
        ]

        for filename in possible_names:

            image_path = (
                image_directory
                / filename
            )

            if image_path.is_file():
                return image_path

        expected_names = {
            name.casefold()
            for name in possible_names
        }

        try:

            for image_path in image_directory.iterdir():

                if not image_path.is_file():
                    continue

                if image_path.suffix.casefold() != ".png":
                    continue

                if (
                    image_path.name.casefold()
                    in expected_names
                ):
                    return image_path

        except OSError:

            return None

        return None

    def _load_car_image(
        self,
    ):
        """
        Load the assigned car's PNG image.

        Returns None when no image exists.
        """

        image_path = (
            self._car_image_path()
        )

        if image_path is None:
            return None

        image = QImage(
            str(image_path)
        )

        if image.isNull():
            return None

        return image

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_text(
        self,
        painter,
        rect,
        text,
        font,
        alignment=(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        ),
    ):

        painter.save()

        painter.setFont(
            font
        )

        painter.setPen(
            Qt.GlobalColor.black
        )

        painter.drawText(
            QRectF(rect),
            Qt.TextFlag.TextWordWrap
            | alignment,
            self._safe_text(
                text
            ),
        )

        painter.restore()

    def _draw_box(
        self,
        painter,
        rect,
        pen_width=1,
    ):

        painter.save()

        painter.setPen(
            QPen(
                Qt.GlobalColor.black,
                pen_width,
            )
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.drawRect(
            QRectF(rect)
        )

        painter.restore()

    def _draw_section_label(
        self,
        painter,
        rect,
        text,
        font,
    ):

        painter.save()

        painter.setFont(
            font
        )

        painter.setPen(
            Qt.GlobalColor.black
        )

        painter.drawText(
            QRectF(rect),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop,
            text,
        )

        painter.restore()

    def _draw_car_image(
        self,
        painter,
        rect,
    ):
        """
        Draw the assigned car image centered within rect.

        The original aspect ratio is preserved.
        """

        if rect.width() <= 1:
            return

        if rect.height() <= 1:
            return

        image = (
            self._load_car_image()
        )

        if image is None:
            return

        pixmap = QPixmap.fromImage(
            image
        )

        if pixmap.isNull():
            return

        scaled_pixmap = pixmap.scaled(
            max(
                1,
                int(rect.width()),
            ),
            max(
                1,
                int(rect.height()),
            ),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        if scaled_pixmap.isNull():
            return

        image_x = (
            rect.x()
            + (
                rect.width()
                - scaled_pixmap.width()
            ) / 2.0
        )

        image_y = (
            rect.y()
            + (
                rect.height()
                - scaled_pixmap.height()
            ) / 2.0
        )

        painter.drawPixmap(
            int(
                round(
                    image_x
                )
            ),
            int(
                round(
                    image_y
                )
            ),
            scaled_pixmap,
        )

    # ------------------------------------------------------------------
    # Main renderer
    # ------------------------------------------------------------------

    def draw(
        self,
        painter,
        rect,
    ):
        """
        Draw the complete waybill inside rect.

        The bottom 25 percent of the form is reserved explicitly
        for the car image.
        """

        painter.save()

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

        x = float(
            rect.x()
        )

        y = float(
            rect.y()
        )

        width = float(
            rect.width()
        )

        height = float(
            rect.height()
        )

        # --------------------------------------------------------------
        # Fonts
        # --------------------------------------------------------------

        title_font = QFont(
            "Arial"
        )
        title_font.setPointSizeF(
            13.0
        )
        title_font.setBold(
            True
        )

        subtitle_font = QFont(
            "Arial"
        )
        subtitle_font.setPointSizeF(
            10.0
        )
        subtitle_font.setBold(
            True
        )

        section_font = QFont(
            "Arial"
        )
        section_font.setPointSizeF(
            7.0
        )
        section_font.setBold(
            True
        )

        value_font = QFont(
            "Arial"
        )
        value_font.setPointSizeF(
            9.0
        )

        value_bold_font = QFont(
            "Arial"
        )
        value_bold_font.setPointSizeF(
            9.5
        )
        value_bold_font.setBold(
            True
        )

        small_font = QFont(
            "Arial"
        )
        small_font.setPointSizeF(
            7.0
        )

        # --------------------------------------------------------------
        # Outer border
        # --------------------------------------------------------------

        self._draw_box(
            painter,
            QRectF(
                x,
                y,
                width,
                height,
            ),
            pen_width=2,
        )

        # --------------------------------------------------------------
        # Reserve image area first
        # --------------------------------------------------------------

        image_section_height = (
            height * 0.25
        )

        content_bottom = (
            y
            + height
            - image_section_height
        )

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------

        header_height = (
            height * 0.145
        )

        header_rect = QRectF(
            x,
            y,
            width,
            header_height,
        )

        self._draw_box(
            painter,
            header_rect,
        )

        self._draw_text(
            painter,
            QRectF(
                x,
                y + height * 0.018,
                width,
                height * 0.040,
            ),
            "MODEL RAILROAD OPERATIONS",
            title_font,
            Qt.AlignmentFlag.AlignCenter,
        )

        self._draw_text(
            painter,
            QRectF(
                x,
                y + height * 0.060,
                width,
                height * 0.038,
            ),
            "FREIGHT WAYBILL",
            subtitle_font,
            Qt.AlignmentFlag.AlignCenter,
        )

        self._draw_text(
            painter,
            QRectF(
                x,
                y + height * 0.102,
                width,
                height * 0.035,
            ),
            f"WAYBILL #{self.waybill.id}",
            subtitle_font,
            Qt.AlignmentFlag.AlignCenter,
        )

        # --------------------------------------------------------------
        # General geometry
        # --------------------------------------------------------------

        current_y = (
            y + header_height
        )

        row_height = (
            height * 0.105
        )

        half_width = (
            width / 2.0
        )

        # --------------------------------------------------------------
        # CAR / CAR TYPE
        # --------------------------------------------------------------

        car_row = QRectF(
            x,
            current_y,
            width,
            row_height,
        )

        self._draw_box(
            painter,
            car_row,
        )

        painter.drawLine(
            x + half_width,
            current_y,
            x + half_width,
            current_y + row_height,
        )

        self._draw_section_label(
            painter,
            QRectF(
                x + width * 0.025,
                current_y + height * 0.012,
                half_width - width * 0.05,
                height * 0.025,
            ),
            "CAR",
            section_font,
        )

        self._draw_text(
            painter,
            QRectF(
                x + width * 0.025,
                current_y + height * 0.040,
                half_width - width * 0.05,
                height * 0.050,
            ),
            self._car_text(
                self.waybill
            ),
            value_bold_font,
        )

        self._draw_section_label(
            painter,
            QRectF(
                x + half_width + width * 0.025,
                current_y + height * 0.012,
                half_width - width * 0.05,
                height * 0.025,
            ),
            "CAR TYPE / STATUS",
            section_font,
        )

        self._draw_text(
            painter,
            QRectF(
                x + half_width + width * 0.025,
                current_y + height * 0.040,
                half_width - width * 0.05,
                height * 0.050,
            ),
            self._car_type_and_status(
                self.waybill
            ),
            value_font,
        )

        current_y += (
            row_height
        )

        # --------------------------------------------------------------
        # ORIGIN / DESTINATION
        # --------------------------------------------------------------

        location_height = (
            height * 0.205
        )

        location_row = QRectF(
            x,
            current_y,
            width,
            location_height,
        )

        self._draw_box(
            painter,
            location_row,
        )

        painter.drawLine(
            x + half_width,
            current_y,
            x + half_width,
            current_y + location_height,
        )

        self._draw_section_label(
            painter,
            QRectF(
                x + width * 0.025,
                current_y + height * 0.012,
                half_width - width * 0.05,
                height * 0.025,
            ),
            "ORIGIN",
            section_font,
        )

        self._draw_text(
            painter,
            QRectF(
                x + width * 0.025,
                current_y + height * 0.040,
                half_width - width * 0.05,
                location_height - height * 0.050,
            ),
            self._origin_text(
                self.waybill
            ),
            value_font,
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop,
        )

        self._draw_section_label(
            painter,
            QRectF(
                x + half_width + width * 0.025,
                current_y + height * 0.012,
                half_width - width * 0.05,
                height * 0.025,
            ),
            "DESTINATION",
            section_font,
        )

        self._draw_text(
            painter,
            QRectF(
                x + half_width + width * 0.025,
                current_y + height * 0.040,
                half_width - width * 0.05,
                location_height - height * 0.050,
            ),
            self._destination_text(
                self.waybill
            ),
            value_bold_font,
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop,
        )

        current_y += (
            location_height
        )

        # --------------------------------------------------------------
        # LOAD / COMMODITY / GROSS WEIGHT
        # --------------------------------------------------------------

        status_height = (
            height * 0.095
        )

        status_row = QRectF(
            x,
            current_y,
            width,
            status_height,
        )

        self._draw_box(
            painter,
            status_row,
        )

        third_width = width / 3.0

        painter.drawLine(
            x + third_width,
            current_y,
            x + third_width,
            current_y + status_height,
        )

        painter.drawLine(
            x + third_width * 2.0,
            current_y,
            x + third_width * 2.0,
            current_y + status_height,
        )

        load_sections = (
            ("MOVEMENT", self._load_state_text(self.waybill)),
            ("COMMODITY", self.waybill.commodity or ""),
            ("GROSS WEIGHT / TONNAGE", self._weight_text(self.waybill)),
        )

        for section_index, (label, value) in enumerate(load_sections):
            section_x = x + third_width * section_index

            self._draw_section_label(
                painter,
                QRectF(
                    section_x + width * 0.015,
                    current_y + height * 0.008,
                    third_width - width * 0.03,
                    height * 0.025,
                ),
                label,
                section_font,
            )

            self._draw_text(
                painter,
                QRectF(
                    section_x + width * 0.015,
                    current_y + height * 0.034,
                    third_width - width * 0.03,
                    height * 0.052,
                ),
                value,
                small_font,
            )

        current_y += (
            status_height
        )

        # --------------------------------------------------------------
        # WAYBILL STATUS / CREATED
        # --------------------------------------------------------------

        status_created_height = (
            height * 0.095
        )

        row = QRectF(
            x,
            current_y,
            width,
            status_created_height,
        )

        self._draw_box(
            painter,
            row,
        )

        painter.drawLine(
            x + half_width,
            current_y,
            x + half_width,
            current_y + status_created_height,
        )

        self._draw_section_label(
            painter,
            QRectF(
                x + width * 0.025,
                current_y + height * 0.012,
                half_width - width * 0.05,
                height * 0.025,
            ),
            "WAYBILL STATUS",
            section_font,
        )

        self._draw_text(
            painter,
            QRectF(
                x + width * 0.025,
                current_y + height * 0.040,
                half_width - width * 0.05,
                height * 0.045,
            ),
            self.waybill.status,
            value_bold_font,
        )

        self._draw_section_label(
            painter,
            QRectF(
                x + half_width + width * 0.025,
                current_y + height * 0.012,
                half_width - width * 0.05,
                height * 0.025,
            ),
            "CREATED",
            section_font,
        )

        self._draw_text(
            painter,
            QRectF(
                x + half_width + width * 0.025,
                current_y + height * 0.040,
                half_width - width * 0.05,
                height * 0.045,
            ),
            self._created_text(
                self.waybill
            ),
            value_font,
        )

        current_y += (
            status_created_height
        )

        # --------------------------------------------------------------
        # NOTES
        # --------------------------------------------------------------

        notes_height = (
            content_bottom
            - current_y
        )

        if notes_height > 1:

            notes_row = QRectF(
                x,
                current_y,
                width,
                notes_height,
            )

            self._draw_box(
                painter,
                notes_row,
            )

            self._draw_section_label(
                painter,
                QRectF(
                    x + width * 0.025,
                    current_y + height * 0.012,
                    width - width * 0.05,
                    height * 0.025,
                ),
                "NOTES",
                section_font,
            )

            notes = (
                self.waybill.notes
                or ""
            )

            self._draw_text(
                painter,
                QRectF(
                    x + width * 0.025,
                    current_y + height * 0.042,
                    width - width * 0.05,
                    max(
                        1.0,
                        notes_height - height * 0.050,
                    ),
                ),
                notes,
                small_font,
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignTop,
            )

        # --------------------------------------------------------------
        # CAR IMAGE
        # --------------------------------------------------------------

        image_rect = QRectF(
            x,
            content_bottom,
            width,
            image_section_height,
        )

        self._draw_box(
            painter,
            image_rect,
        )

        #
        # Temporary diagnostic label.
        #

        self._draw_text(
            painter,
            QRectF(
                x + width * 0.025,
                content_bottom + height * 0.010,
                width - width * 0.050,
                height * 0.030,
            ),
            "CAR IMAGE",
            section_font,
            Qt.AlignmentFlag.AlignCenter,
        )

        image_draw_rect = QRectF(
            x + width * 0.025,
            content_bottom + height * 0.045,
            width - width * 0.050,
            image_section_height - height * 0.055,
        )

        self._draw_car_image(
            painter,
            image_draw_rect,
        )

        painter.restore()
