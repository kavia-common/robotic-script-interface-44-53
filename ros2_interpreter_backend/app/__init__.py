from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})

# API Configuration
app.config["API_TITLE"] = "ROS2 Lua-like Interpreter API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config['OPENAPI_URL_PREFIX'] = '/docs'
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Initialize API
api = Api(app)

# Register blueprints
from .routes.health import blp as health_blp
from .routes.interpreter import blp as interpreter_blp
from .routes.plugins import blp as plugins_blp
from .routes.ros2 import blp as ros2_blp

api.register_blueprint(health_blp)
api.register_blueprint(interpreter_blp)
api.register_blueprint(plugins_blp)
api.register_blueprint(ros2_blp)
