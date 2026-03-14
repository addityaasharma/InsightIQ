import uuid
from supabase import create_client

SUPABASE_URL = "https://fhullklhjouoyeqgdkhu.supabase.co"
SUPABASE_KEY = "sb_publishable_8b_DkLu9yshfTCxbWTA8BQ_6yNEkj8f"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_csv_to_supabase(file):
    filename = f"{uuid.uuid4()}.csv"
    supabase.storage.from_("datasets").upload(
        filename,
        file.read(),
        {"content-type": "text/csv"},
    )
    url = supabase.storage.from_("datasets").get_public_url(filename)
    return url