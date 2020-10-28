from config import DEBUG, DB_ENGINE

from sqlalchemy import Column, DateTime, VARCHAR,Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


engine = create_engine(DB_ENGINE, echo=DEBUG)


class PersonTimeChecker(Base):
    __tablename__ = 'coming_leaving'

    partner_id = Column(Integer, primary_key=True)
    full_name = Column(VARCHAR(255), nullable=False)
    coming_datetime = Column(DateTime, nullable=False)
    leaving_datetime = Column(DateTime, nullable=False)
    report_id = Column(Integer, nullable=False, unique=False)


Base.metadata.create_all(engine)


Session = sessionmaker(bind=engine)
Session.configure(bind=engine)

