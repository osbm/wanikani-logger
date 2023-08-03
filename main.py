import requests
import pandas as pd
from dotenv import load_dotenv

import os
import json
import datetime
import huggingface_hub

load_dotenv()

WANIKANI_TOKEN = os.getenv("WANIKANI_ACCESS_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

TODAY = datetime.date.today().isoformat()

def get_all_pages(url):
    headers = {
        "Wanikani-Revision": "20170710",
        "Authorization": f"Bearer {WANIKANI_TOKEN}"
    }
    
    all_data = []
    next_url = url

    while next_url:
        response = requests.get(next_url, headers=headers)
        json_response = response.json()
        data = json_response["data"]
        all_data.extend(data)

        next_url = json_response["pages"]["next_url"]

    return all_data


def save_reviews():
    all_review_statistics = get_all_pages('https://api.wanikani.com/v2/review_statistics')

    reviews = []

    for data in all_review_statistics:

        review_type = data["data"]["subject_type"]

        row = {
            "review_id": data["id"],
            "created_at": data["data"]["created_at"],
            "data_updated_at": data["data_updated_at"],
            "subject_type": review_type,
            "subject_id": data["data"]["subject_id"],
            "hidden": data["data"]["hidden"],
            "percentage_correct": data["data"]["percentage_correct"],
            "meaning_correct": data["data"]["meaning_correct"],
            "meaning_current_streak": data["data"]["meaning_current_streak"],
            "meaning_incorrect": data["data"]["meaning_incorrect"],
            "meaning_max_streak": data["data"]["meaning_max_streak"],
        }

        if review_type in ["kanji", "vocabulary"]: # have reading
            row['reading_correct'] = data["data"]["reading_correct"]
            row['reading_current_streak'] = data["data"]["reading_current_streak"]
            row['reading_incorrect'] = data["data"]["reading_incorrect"]
            row['reading_max_streak'] = data["data"]["reading_max_streak"]

        reviews.append(row)

    reviews_df = pd.DataFrame(reviews)
    reviews_df.to_csv(f'{TODAY}_reviews.csv', index=False)



def save_study_materials():
    all_study_materials = get_all_pages("https://api.wanikani.com/v2/study_materials")
    if len(all_study_materials) == 0:
        return
    study_materials = []

    for data in all_study_materials:
        study_materials.append(
            {
                "data_updated_at": data["data_updated_at"],
                "created_at": data["data"]["created_at"],
                "subject_id": data["data"]["subject_id"],
                "subject_type": data["data"]["subject_type"],
                "meaning_note": data["data"]["meaning_note"],
                "reading_note": data["data"]["reading_note"],
                "meaning_synonyms": str(tuple(data["data"]["reading_note"])),
            }
        )

    study_materials_df = pd.DataFrame(study_materials)
    study_materials_df.to_csv(f'{TODAY}_study_materials.csv', index=False)


def save_level_progressions():
    level_progressions = get_all_pages("https://api.wanikani.com/v2/level_progressions")
    rows = []


    for data in level_progressions:

        rows.append(
            {
                "level": data["data"]["level"],
                "created_at": data["data"]["created_at"],
                "unlocked_at": data["data"]["unlocked_at"],
                "started_at": data["data"]["started_at"],
                "passed_at": data["data"]["passed_at"],
                "completed_at": data["data"]["completed_at"],
                "abandoned_at": data["data"]["abandoned_at"],
            }
        )

    level_progressions_df = pd.DataFrame(rows)
    level_progressions_df.to_csv(f"{TODAY}_level_progressions.csv", index=False)


def save_subjects():

    with open('everything.json', 'w') as outfile:
        json.dump(get_all_pages("https://api.wanikani.com/v2/subjects"), outfile)

    
    for subject_type in ['radical', 'kanji', 'kana_vocabulary', 'vocabulary']:
        with open(f'{subject_type}.json', 'w') as outfile:
            json.dump(get_all_pages(f"https://api.wanikani.com/v2/subjects?types={subject_type}"), outfile)


if __name__ == "__main__":

    save_reviews()
    print("Reviews Done")
    # save_study_materials()
    # print("Study Materials Done")
    save_subjects()
    print("Subjects Done")
    save_level_progressions()
    print("Level Progressions Done")

    api = huggingface_hub.HfApi()

    # level progressions
    api.upload_file(
        path_or_fileobj=f"{TODAY}_level_progressions.csv",
        path_in_repo=f"level_progressions/{TODAY}_level_progressions.csv",
        repo_id="osbm/wanikani-logs",
        repo_type="dataset",
        token=HF_TOKEN,
    )

    # reviews
    api.upload_file(
        path_or_fileobj=f"{TODAY}_reviews.csv",
        path_in_repo=f"reviews/{TODAY}_reviews.csv",
        repo_id="osbm/wanikani-logs",
        repo_type="dataset",
        token=HF_TOKEN,
    )

    # study materials
    # if os.path.exists(f"{TODAY}_study_materials.csv"):
    #     api.upload_file(
    #         path_or_fileobj=f"{TODAY}_study_materials.csv",
    #         path_in_repo=f"study_materials/{TODAY}_study_materials.csv",
    #         repo_id="osbm/wanikani-logs",
    #         repo_type="dataset",
    #         token=HF_TOKEN,
    #     )

    api.upload_folder(
        repo_id="osbm/wanikani-dataset",
        repo_type="dataset",
        folder_path=".",
        allow_patterns="*.json",
        token=HF_TOKEN,
        
    )

