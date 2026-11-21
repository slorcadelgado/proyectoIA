import vertexai
from vertexai.tuning import sft
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = "summer-surfer-344819"
LOCATION = "us-central1"
vertexai.init(project=PROJECT_ID, location=LOCATION)

tuning_job_id = "2447604495081799680"
job = sft.SupervisedTuningJob(
    f"projects/{PROJECT_ID}/locations/{LOCATION}/tuningJobs/{tuning_job_id}"
)
job.cancel()