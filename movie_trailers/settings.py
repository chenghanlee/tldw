class Config(object):
    # AMAZON
    AWS_ACCESS_KEY = 'AKIAJQ3N2TVP5EAVVLJA'
    AWS_SECRET_KEY = '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'
    AWS_AFFILIATE_KEY = 'helppme-20'

    #SWYFTYPE
    SW_EMAIL = "lee.chenghan@gmail.com"
    SW_PASSWORD = "Hnaoa6hW!"
    SW_API_KEY = 'S1xhxcq9PH8VBPqGPCNy'
    SW_ENGINE_SLUG = 'tldw'

    #API
    ROTTEN_TOMATOES_API_KEY = 'n298xcf5bkxf4qtnbmw7364x'
    TMDB_API_KEY = 'f43cd8f01703edd5a67e40027e5d4055'

    # AWS
    BUCKET = 'trading_spaces'



class ProdConfig(Config):
    DEBUG = False
    MONGODB_SETTINGS = {"DB": "admission_for_one",
                        "USERNAME": "lee.chenghan@gmail.com",
                        "PASSWORD": "Hnaoa6hW!",
                        "HOST": "rose.mongohq.com",
                        "PORT": 10083}
class DevConfig(Config):
    DEBUG = True
    DEBUG_TB_PANELS = ('flask.ext.mongoengine.panels.MongoDebugPanel',)
    MONGODB_SETTINGS = {"DB": "admission_for_one",
                        "USERNAME": "lee.chenghan@gmail.com",
                        "PASSWORD": "Hnaoa6hW!",
                        "HOST": "rose.mongohq.com",
                        "PORT": 10083}

class CeleryConfig(Config):
    BROKER_TRANSPORT = 'sqs'
    BROKER_TRANSPORT_OPTIONS = {
        'polling_interval': 60,
        'region': 'us-east-1'
    }
    BROKER_USER = Config.AWS_ACCESS_KEY
    BROKER_PASSWORD = Config.AWS_SECRET_KEY
    CELERY_DEFAULT_RATE_LIMIT = '1/m'
    CELERY_DEFAULT_QUEUE = 'default'
    CELERY_QUEUES = {
        'default': {
            "exchange": "default",
            "binding_key": "default",
        },
        'movie_stats': {
            'exchange': 'movie_stats',
            'routing_key': 'movie_stats',
        },
        'movie_crawler': {
            'exchange': 'movie_crawler',
            'routing_key': 'movie_crawler',
        }
    }
    # CELERYD_PREFETCH_MULTIPLIER = 0