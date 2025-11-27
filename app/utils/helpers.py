#RETURN BY FACILITY TYPE
def get_services_by_type(facility_type):
    services = {
        'Hospital': [
            'Emergency Services',
            'Inpatient Care',
            'Outpatient Services',
            'Surgery',
            'Maternity Services',
            'Laboratory Services',
            'Pharmacy',
            'X-Ray/Imaging',
            'Ambulance Services'
        ],
        'Health Centre': [
            'Outpatient Services',
            'Maternity Services',
            'Child Health Services',
            'HIV Testing & Treatment',
            'TB Services',
            'Pharmacy',
            'Laboratory Services'
        ],
        'Clinic': [
            'Basic Consultation',
            'Immunization',
            'Family Planning',
            'Antenatal Care',
            'HIV Testing',
            'Minor Treatments'
        ],
        'Dispensary': [
            'Basic Consultation',
            'Medication Distribution',
            'Immunization',
            'First Aid'
        ]
    }
    return services.get(facility_type, ['General Health Services'])

#RETURN BY WORKING HOURS
def get_working_hours(facility_type):
    if facility_type == 'Hospital':
        return {
            'weekdays': '24 Hours',
            'weekends': '24 Hours',
            'emergency': '24/7 Available'
        }
    elif facility_type in ['Health Centre', 'Clinic']:
        return {
            'weekdays': '7:30 AM - 4:30 PM',
            'saturday': '7:30 AM - 12:00 PM',
            'sunday': 'Closed',
            'emergency': 'Limited emergency services'
        }
    else:
        return {
            'weekdays': '8:00 AM - 4:00 PM',
            'weekends': 'Closed',
            'emergency': 'Refer to nearest hospital'
        }

#MOCK INFO
def get_contact_info(district):
    return {
        'phone': '+265 1 XXX XXX',
        'email': f'{district.lower().replace(" ", "")}@health.gov.mw',
        'district_office': f'{district} District Health Office'
    }
