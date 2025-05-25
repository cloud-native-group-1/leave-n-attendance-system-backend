import os
from dotenv import load_dotenv
import json
import tempfile

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/postgres")
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
    BUCKET_KEY = os.getenv("BUCKET_KEY")  # CI/CD 用的 JSON 字串

    @classmethod
    def setup_gcp_credentials(cls):
        """
        本地若有 bucket_key.json，直接設環境變數指向檔案路徑。
        CI/CD 環境，從 BUCKET_KEY 讀 JSON 字串，動態寫入暫存檔並設環境變數。
        """
        local_key_path = "app/bucket_key.json"
        if os.path.exists(local_key_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_key_path
            print(f"Using local GCP credential file: {local_key_path}")
        else:
            if not cls.BUCKET_KEY:
                raise RuntimeError("BUCKET_KEY env var is missing and local credential file not found.")
            
            gcp_json = json.loads(cls.BUCKET_KEY)
            temp_cred_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            temp_cred_file.write(json.dumps(gcp_json).encode("utf-8"))
            temp_cred_file.flush()
            temp_cred_file.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_cred_file.name
            print(f"Created temp GCP credential file at: {temp_cred_file.name}")

Settings.setup_gcp_credentials()
settings = Settings()
