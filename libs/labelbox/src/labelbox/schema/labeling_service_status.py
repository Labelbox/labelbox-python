from enum import Enum


class LabelingServiceStatus(Enum):
    Accepted = 'ACCEPTED'
    Calibration = 'CALIBRATION'
    Complete = 'COMPLETE'
    Production = 'PRODUCTION'
    Requested = 'REQUESTED'
    SetUp = 'SET_UP'
