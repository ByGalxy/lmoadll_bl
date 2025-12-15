# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
响应处理

统一处理响应
"""
from flask import jsonify
from functools import wraps


class ResponseHandler:
    def __init__(self):
        self.success_code = 200
        self.custom_error_code = 233
        self.error_code = 500

    def success_response(self, data=None, message="OK"):
        return jsonify({
            "code": self.success_code,
            "message": message,
            "data": data
        })

    def custom_error_response(self, message="ERROR", data=None):
        return jsonify({
            "code": self.custom_error_code,
            "message": message,
            "data": data or {}
        }), self.custom_error_code

    def error_response(self, message="ERROR", data=None):
        return jsonify({
            "code": self.error_code,
            "message": message,
            "data": data or {}
        }), self.error_code

    def response_middleware(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                if isinstance(result, tuple) and len(result) == 2:
                    response_data, status_code = result
                    if status_code == self.custom_error_code:
                        return response_data
                    
                    if status_code == self.success_code:
                        return self.success_response(response_data)
                
                if isinstance(result, dict) or isinstance(result, list):
                    return self.success_response(result)
                
                return result
                
            except Exception as error:
                return self.error_response(str(error))
        
        return wrapper


response_handler = ResponseHandler()
