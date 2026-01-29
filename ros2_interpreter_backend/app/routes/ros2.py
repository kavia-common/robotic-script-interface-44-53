"""
ROS2 Integration API Routes

REST endpoints for ROS2 topic publishing, subscribing, and service calls
"""

from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request
from marshmallow import Schema, fields
import logging

logger = logging.getLogger(__name__)

blp = Blueprint(
    "ROS2",
    "ros2",
    url_prefix="/api/ros2",
    description="ROS2 integration endpoints for topics, services, and messaging"
)


class PublishMessageSchema(Schema):
    """Schema for publishing ROS2 message"""
    topic = fields.Str(required=True, description="Topic name")
    message = fields.Dict(required=True, description="Message data")
    msg_type = fields.Str(description="ROS2 message type", missing="std_msgs/String")


class ServiceCallSchema(Schema):
    """Schema for ROS2 service call"""
    service = fields.Str(required=True, description="Service name")
    request = fields.Dict(required=True, description="Service request data")


class TopicListResponseSchema(Schema):
    """Schema for topic list response"""
    topics = fields.List(fields.Str(), description="List of active topics")
    count = fields.Int(description="Number of topics")


class ServiceListResponseSchema(Schema):
    """Schema for service list response"""
    services = fields.List(fields.Str(), description="List of available services")
    count = fields.Int(description="Number of services")


@blp.route("/status")
class ROS2Status(MethodView):
    """
    Get ROS2 bridge status
    """
    
    @blp.response(200)
    def get(self):
        """
        Get ROS2 bridge status and configuration
        
        Returns information about the ROS2 bridge initialization status,
        active topics, services, and connection details.
        """
        from .interpreter import ros2_bridge
        
        return {
            'initialized': ros2_bridge.is_initialized,
            'node_name': ros2_bridge.node_name,
            'topics': ros2_bridge.get_topic_list(),
            'services': ros2_bridge.get_service_list(),
            'publishers': len(ros2_bridge.publishers),
            'subscribers': len(ros2_bridge.subscribers)
        }


@blp.route("/publish")
class PublishMessage(MethodView):
    """
    Publish a message to a ROS2 topic
    """
    
    @blp.arguments(PublishMessageSchema)
    @blp.response(200)
    def post(self, data):
        """
        Publish message to ROS2 topic
        
        Publishes a message to the specified ROS2 topic. Creates
        the publisher if it doesn't exist.
        """
        from .interpreter import ros2_bridge
        
        topic = data['topic']
        message = data['message']
        msg_type = data.get('msg_type', 'std_msgs/String')
        
        success = ros2_bridge.publish(topic, message, msg_type)
        
        if success:
            return {
                'success': True,
                'message': f'Published to topic: {topic}',
                'topic': topic
            }
        else:
            return {
                'success': False,
                'message': 'Failed to publish message'
            }, 500


@blp.route("/topics")
class TopicList(MethodView):
    """
    List all active ROS2 topics
    """
    
    @blp.response(200, TopicListResponseSchema)
    def get(self):
        """
        Get list of active ROS2 topics
        
        Returns all topics that have been published to or subscribed
        from through this bridge.
        """
        from .interpreter import ros2_bridge
        
        topics = ros2_bridge.get_topic_list()
        
        return {
            'topics': topics,
            'count': len(topics)
        }


@blp.route("/services")
class ServiceList(MethodView):
    """
    List all available ROS2 services
    """
    
    @blp.response(200, ServiceListResponseSchema)
    def get(self):
        """
        Get list of available ROS2 services
        
        Returns all services that have been created or are available
        through this bridge.
        """
        from .interpreter import ros2_bridge
        
        services = ros2_bridge.get_service_list()
        
        return {
            'services': services,
            'count': len(services)
        }


@blp.route("/call")
class ServiceCall(MethodView):
    """
    Call a ROS2 service
    """
    
    @blp.arguments(ServiceCallSchema)
    @blp.response(200)
    def post(self, data):
        """
        Call a ROS2 service
        
        Calls the specified ROS2 service with the provided request data
        and returns the service response.
        """
        from .interpreter import ros2_bridge
        
        service = data['service']
        request = data['request']
        
        response = ros2_bridge.call_service(service, request)
        
        if response:
            return {
                'success': True,
                'service': service,
                'response': response
            }
        else:
            return {
                'success': False,
                'message': f'Failed to call service: {service}'
            }, 500


@blp.route("/messages")
class MessageHistory(MethodView):
    """
    Get recent message history
    """
    
    @blp.response(200)
    def get(self):
        """
        Get recent message history
        
        Returns the history of recent messages published through
        the ROS2 bridge.
        """
        from .interpreter import ros2_bridge
        
        limit = request.args.get('limit', default=100, type=int)
        messages = ros2_bridge.get_message_history(limit)
        
        return {
            'messages': messages,
            'count': len(messages)
        }
