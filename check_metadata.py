import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.database.base import Base

# Import all models
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack


for table_name, table in Base.metadata.tables.items():
    print("\nTABLE:", table_name)

    print("Constraints:")
    for constraint in table.constraints:
        print("  ", constraint)
