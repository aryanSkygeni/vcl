import azure.functions as func
import json
import logging
from validate_change_logs_project import process_controller
import asyncio

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="vcl_http_trigger")
def vcl_http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Received API request.")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON format", status_code=400)
    
    # Validate request data
    validation_message, is_valid = validate_request_data(req_body)
    if not is_valid:
        return func.HttpResponse(validation_message, status_code=400)

    process_controller.vcl_process_controller(req_body)
    return func.HttpResponse("Message received", status_code=202)

def validate_request_data(req_body):
    """ Validate JSON request data """
    required_fields = ["schema", "required_ch_opps_flag", "replicate_lkp_stages_new", "explicit_execution"]
    
    # check length of the request body
    if len(req_body)!=4:
        return f"Total fields not 4", False
    # Check if all required fields exist
    for field in required_fields:
        if field not in req_body:
            return f"Missing required field: {field}", False
    
    # Validate data types
    if not isinstance(req_body["schema"], str):
        return "Invalid data type: 'schema' must be a string", False
    if not all(isinstance(req_body[field], bool) for field in required_fields if field != "schema"):
        return "Invalid data type: All fields except 'schema' must be boolean", False
    
    return "Validation successful", True