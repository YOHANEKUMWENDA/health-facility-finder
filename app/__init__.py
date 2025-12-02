from flask import Flask
from flask_cors import CORS
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app)
    
    #REGISTER BLUE PRINTS
    from app.routes.main import main_bp
    from app.routes.facilities import facilities_bp
    from app.routes.locations import locations_bp
    from app.routes.stats import stats_bp
    from app.routes.routing import routing_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(facilities_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(routing_bp)
    
    return app
