import csv
import pandas as pd



#First, I know that I need some sort of filtering ability. So I'll turn it into a parametrized function.
def select_cohort(modifiers_kept=None, max_undetected_frac=0.5, min_duration_sec=0.0):
    if modifiers_kept == None:
        modifiers_kept = {"clean"}
    df = pd.read_csv("_data/megalb.csv")

    df["undetected_frac"] = df["n_undetected"] / df["n_frames"] # The dataframe now also has a new column that will be preserved when I pass it on!

    filtered_df = df[
        (df["modifier"].isin(modifiers_kept)) & 
        (df["undetected_frac"] <= max_undetected_frac) & 
        (df["duration_sec"] >= min_duration_sec)
    ]

    print(f"Total filtered rows: {len(filtered_df)}")
    return filtered_df


# Man... that's it? That was quick
#it ended up being a little less quick (45 min more) but vastly more satisfying!

select_cohort()
        

# Now for part 2. 

def partb(filtered_df):
    

        