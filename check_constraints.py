from sqlalchemy import inspect
from modelrailroadops.database.database import engine


inspector = inspect(engine)

print("Industry constraints:")
for item in inspector.get_unique_constraints("industries"):
    print(item)

print("\nIndustry Track constraints:")
for item in inspector.get_unique_constraints("industry_tracks"):
    print(item)