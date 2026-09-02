# Train Route Table Model


from PySide6.QtCore import (
    QAbstractTableModel,
    Qt,
)


class TrainRouteTableModel(QAbstractTableModel):
    """
    Table model used to display Train route stops.

    Route records are supplied through set_routes().
    The model does not modify the database.
    """

    HEADERS = [
        "Seq",
        "Location",
        "Track",
        "Traffic Use",
        "Description",
    ]

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.routes = []

    #
    # Row count
    #

    def rowCount(
        self,
        parent=None,
    ):

        if (
            parent is not None
            and parent.isValid()
        ):

            return 0

        return len(
            self.routes
        )

    #
    # Column count
    #

    def columnCount(
        self,
        parent=None,
    ):

        if (
            parent is not None
            and parent.isValid()
        ):

            return 0

        return len(
            self.HEADERS
        )

    #
    # Header
    #

    def headerData(
        self,
        section,
        orientation,
        role=Qt.DisplayRole,
    ):

        if role != Qt.DisplayRole:

            return None

        if orientation == Qt.Horizontal:

            if (
                0
                <= section
                < len(
                    self.HEADERS
                )
            ):

                return self.HEADERS[
                    section
                ]

        if orientation == Qt.Vertical:

            return str(
                section + 1
            )

        return None

    #
    # Data
    #

    def data(
        self,
        index,
        role=Qt.DisplayRole,
    ):

        if not index.isValid():

            return None

        row = index.row()

        column = index.column()

        if (
            row < 0
            or row >= len(
                self.routes
            )
        ):

            return None

        if (
            column < 0
            or column >= len(
                self.HEADERS
            )
        ):

            return None

        route = self.routes[
            row
        ]

        #
        # Display role
        #

        if role == Qt.DisplayRole:

            if column == 0:

                value = (
                    route.sequence
                    if route.sequence is not None
                    else ""
                )

            elif column == 1:

                value = (
                    route.location
                    or ""
                )

            elif column == 2:

                value = (
                    route.operating_track.name
                    if route.operating_track is not None
                    else ""
                )

            elif column == 3:

                value = (
                    route.operating_track.traffic_use.title()
                    if route.operating_track is not None
                    else ""
                )

            elif column == 4:

                value = (
                    route.description
                    or ""
                )

            else:

                return None

            return str(
                value
            )

        #
        # Text alignment
        #

        if role == Qt.TextAlignmentRole:

            if column == 0:

                return (
                    Qt.AlignCenter
                    | Qt.AlignVCenter
                )

            return (
                Qt.AlignLeft
                | Qt.AlignVCenter
            )

        #
        # Sorting role
        #

        if role == Qt.UserRole:

            if column == 0:

                return (
                    route.sequence
                    if route.sequence is not None
                    else 0
                )

            if column == 1:

                return (
                    route.location
                    or ""
                ).casefold()

            if column == 2:

                return (
                    route.operating_track.name
                    if route.operating_track is not None
                    else ""
                ).casefold()

            if column == 3:

                return (
                    route.operating_track.traffic_use
                    if route.operating_track is not None
                    else ""
                ).casefold()

            if column == 4:

                return (
                    route.description
                    or ""
                ).casefold()

        return None

    #
    # Set routes
    #

    def set_routes(
        self,
        routes,
    ):

        routes = list(
            routes
            or []
        )

        self.beginResetModel()

        self.routes = routes

        self.endResetModel()

    #
    # Get route
    #

    def get_route(
        self,
        row,
    ):

        if (
            row < 0
            or row >= len(
                self.routes
            )
        ):

            return None

        return self.routes[
            row
        ]

    #
    # Get route ID
    #

    def get_route_id(
        self,
        row,
    ):

        route = self.get_route(
            row
        )

        if route is None:

            return None

        return route.id
