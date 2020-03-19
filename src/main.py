from scraper import get_url
from inspections import create_csv as create_inspections_csv
from patients import create_csv as create_patients_csv
from querents import create_csv as create_querents_csv

patients_url, querents_url, inspections_url = get_url()
create_patients_csv(patients_url)
create_inspections_csv(inspections_url)
create_querents_csv(querents_url)
