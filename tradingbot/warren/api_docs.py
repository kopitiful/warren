"""
Warren Buffett Newsletter API Documentation
OpenAPI 3.0.0 Specification
"""

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Warren Buffett Newsletter API",
        "version": "1.0.0",
        "description": "REST API for Warren Buffett Investment Newsletter Platform",
        "contact": {
            "name": "Support",
            "email": "support@buffettpicks.com"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Local development"
        },
        {
            "url": "https://api.buffettpicks.com",
            "description": "Production API"
        }
    ],
    "paths": {
        "/api/subscribe": {
            "post": {
                "summary": "Create new subscription",
                "description": "Subscribe to Warren Buffett Newsletter (Free or Premium)",
                "tags": ["Subscriptions"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email", "name", "tier", "market"],
                                "properties": {
                                    "email": {
                                        "type": "string",
                                        "format": "email",
                                        "example": "user@example.com"
                                    },
                                    "name": {
                                        "type": "string",
                                        "example": "John Doe"
                                    },
                                    "tier": {
                                        "type": "string",
                                        "enum": ["free", "premium"],
                                        "description": "Subscription tier"
                                    },
                                    "market": {
                                        "type": "string",
                                        "enum": ["us", "eu"],
                                        "description": "Stock market focus"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Subscription created. Confirmation email sent.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request (missing fields, invalid tier/market)"
                    }
                }
            }
        },
        "/confirm/{token}": {
            "get": {
                "summary": "Confirm email subscription",
                "description": "Confirm email address using confirmation token",
                "tags": ["Subscriptions"],
                "parameters": [
                    {
                        "name": "token",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Email confirmation token"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Email confirmed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "message": {"type": "string"},
                                        "tier": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Invalid confirmation token"
                    }
                }
            }
        },
        "/api/paypal/create-order": {
            "post": {
                "summary": "Create PayPal order",
                "description": "Initiate PayPal payment for Premium subscription",
                "tags": ["Payments"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "subscriber_id": {
                                        "type": "integer",
                                        "example": 1
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Order created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "orderId": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Subscriber not found"
                    },
                    "500": {
                        "description": "PayPal error"
                    }
                }
            }
        },
        "/api/paypal/capture-order": {
            "post": {
                "summary": "Capture PayPal payment",
                "description": "Complete PayPal payment and activate subscription",
                "tags": ["Payments"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "orderId": {"type": "string"},
                                    "subscriber_id": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Payment successful"
                    },
                    "400": {
                        "description": "Payment failed"
                    }
                }
            }
        },
        "/api/subscribers/{subscriber_id}/unsubscribe": {
            "post": {
                "summary": "Unsubscribe from newsletter",
                "description": "Deactivate subscription",
                "tags": ["Subscriptions"],
                "parameters": [
                    {
                        "name": "subscriber_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Unsubscribed successfully"
                    },
                    "404": {
                        "description": "Subscriber not found"
                    }
                }
            }
        },
        "/admin/stats": {
            "get": {
                "summary": "Get subscription statistics",
                "description": "Admin endpoint: Get subscriber metrics",
                "tags": ["Admin"],
                "responses": {
                    "200": {
                        "description": "Statistics retrieved",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total": {"type": "integer"},
                                        "confirmed": {"type": "integer"},
                                        "active": {"type": "integer"},
                                        "free": {"type": "integer"},
                                        "premium": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Subscriber": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string"},
                    "tier": {"type": "string", "enum": ["free", "premium"]},
                    "market": {"type": "string", "enum": ["us", "eu"]},
                    "is_confirmed": {"type": "boolean"},
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "confirmed_at": {"type": "string", "format": "date-time", "nullable": True},
                    "last_newsletter_sent": {"type": "string", "format": "date-time", "nullable": True}
                }
            },
            "NewsletterLog": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "subscriber_id": {"type": "integer"},
                    "sent_at": {"type": "string", "format": "date-time"},
                    "market": {"type": "string"},
                    "top_5_stocks": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
    },
    "tags": [
        {
            "name": "Subscriptions",
            "description": "Manage newsletter subscriptions"
        },
        {
            "name": "Payments",
            "description": "PayPal payment processing"
        },
        {
            "name": "Admin",
            "description": "Administrative endpoints"
        }
    ]
}


# Flask route to expose OpenAPI spec
def add_openapi_endpoint(app):
    @app.route('/api/openapi.json', methods=['GET'])
    def openapi_spec():
        from flask import jsonify
        return jsonify(OPENAPI_SPEC)
    
    @app.route('/api/docs', methods=['GET'])
    def swagger_ui():
        """Swagger UI for API documentation"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Warren Buffett Newsletter API</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.min.css">
            <style>
                html {
                    box-sizing: border-box;
                    overflow: -moz-scrollbars-vertical;
                    overflow-y: scroll;
                }
                *,
                *:before,
                *:after {
                    box-sizing: inherit;
                }
                body {
                    margin:0;
                    background: #fafafa;
                }
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.min.js"></script>
            <script>
                SwaggerUIBundle({
                    url: "/api/openapi.json",
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                })
            </script>
        </body>
        </html>
        '''
