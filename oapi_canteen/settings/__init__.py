from decouple import config

DJANGO_ENVIRONMENT = config('DJANGO_SETTINGS_MODULE', default='oapi_canteen.settings.development')
