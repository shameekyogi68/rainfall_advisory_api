import os
import sys
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Index
from sqlalchemy.orm import declarative_base, sessionmaker

# Add parent directory to path to access config if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import getpass

# Database Connection
# Default to current user for local dev (no password)
default_user = getpass.getuser()
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://{default_user}@localhost:5432/rainfall_db")

Base = declarative_base()

class RainfallHistory(Base):
    __tablename__ = 'rainfall_history'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    taluk = Column(String, nullable=False)
    rainfall_mm = Column(Float, nullable=False)
    
    # Index for fast lookups by taluk and date
    __table_args__ = (Index('idx_rainfall_taluk_date', 'taluk', 'date'),)

class WeatherDrivers(Base):
    __tablename__ = 'weather_drivers'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    taluk = Column(String, nullable=False)
    temp = Column(Float)
    humidity = Column(Float)
    wind = Column(Float)
    pressure = Column(Float)
    
    # Index for fast lookups
    __table_args__ = (Index('idx_weather_taluk_date', 'taluk', 'date'),)

def migrate():
    print("="*60)
    print("🚀 Starting Database Migration")
    print(f"Target DB: {DATABASE_URL}")
    print("="*60)
    
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully.")
    except Exception as e:
        print(f"❌ Could not connect to database: {e}")
        print("Please ensure PostgreSQL is running and DATABASE_URL is set.")
        return

    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. Migrate Rainfall Data
    rainfall_csv = "rainfall_daily_historical_v1.csv"
    if os.path.exists(rainfall_csv):
        print(f"\nProcessing {rainfall_csv}...")
        df = pd.read_csv(rainfall_csv)
        
        # Standardize columns
        # CSV: date, taluk, rainfall
        # DB: date, taluk, rainfall_mm
        df = df.rename(columns={'rainfall': 'rainfall_mm'})
        df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date
        
        # Check if data already exists
        count = session.query(RainfallHistory).count()
        if count > 0:
            print(f"⚠️  Rainfall table already has {count} rows. Skipping insertion.")
        else:
            print(f"Insertion {len(df)} rows into rainfall_history...")
            df.to_sql('rainfall_history', engine, if_exists='append', index=False, chunksize=1000)
            print("✅ Rainfall data migrated.")
    else:
        print(f"❌ File not found: {rainfall_csv}")

    # 2. Migrate Weather Drivers
    weather_csv = "weather_drivers_daily_v1.csv"
    if os.path.exists(weather_csv):
        print(f"\nProcessing {weather_csv}...")
        df = pd.read_csv(weather_csv)
        
        # Standardize columns
        # CSV: date, temp, humidity, wind, pressure, taluk
        # DB matches exactly (except 'date' type)
        df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date
        
        # Check if data already exists
        count = session.query(WeatherDrivers).count()
        if count > 0:
            print(f"⚠️  Weather table already has {count} rows. Skipping insertion.")
        else:
            print(f"Insertion {len(df)} rows into weather_drivers...")
            df.to_sql('weather_drivers', engine, if_exists='append', index=False, chunksize=1000)
            print("✅ Weather data migrated.")
    else:
        print(f"❌ File not found: {weather_csv}")
        
    session.close()
    print("\n🎉 Migration Complete!")

if __name__ == "__main__":
    migrate()
