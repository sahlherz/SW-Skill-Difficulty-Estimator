import sys
from pathlib import Path

# Adds the project root (one level above CV/) to Python's search path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _scripts.featurizing.compute_joint_angle import angle
from CV.loader import load_sequence
import pandas as pd






if __name__ == "__main__":
    df = pd.read_csv("_data/megalb.csv")
    filtered_df = df[df["uid"] == "IAAQEyPks4dMzTOWRfwQziCxHXk1"]
    for row in filtered_df.itertuples():
        seq = load_sequence(row)

        anglesRight = angle(seq, 16, 14, 12) # right wrist, elbow, shoulder
        anglesLeft = angle(seq, 15, 13, 11) # left wrist, elbow, shoulder

        print(min(anglesRight))
        print(max(anglesRight))
        print(min(anglesLeft))
        print(max(anglesLeft))

