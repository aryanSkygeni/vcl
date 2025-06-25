import azure.functions as func
import json
import logging
from validate_change_logs_project import process_controller
import asyncio

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="vcl_http_trigger")
def vcl_http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    ## log start of VCL
    logging.info("Received API request. Starting VCL")

    ## Test wether req format is valid
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON format", status_code=400)
    
    ## Validate request data
    validation_message, is_valid = validate_request_data(req_body)
    if not is_valid:
        return func.HttpResponse(validation_message, status_code=400)

    ## execute VCL
    vcl_status = process_controller.vcl_process_controller(req_body)
    
    ## handle vcl_status and return response to event handler (if scheduled execution)
    logging.info(f"VCL completed for schema: {req_body['schema']}")
    if vcl_status == 'SUCCESS':
        return func.HttpResponse("Processed VCL successfully", status_code=200)
    elif vcl_status == 'FAILED_WITH_LOG_ERROR':
        return func.HttpResponse("Processed VCL successfully with LOG ERRORS", status_code=200)
    elif vcl_status == 'FAILED_WITH_OTHER_ERROR':
        return func.HttpResponse("Error in processing VCL: Failed to acquire Lock", status_code=200)
    else:
        return func.HttpResponse("Error in processing VCL: FAILED_WITH_OTHER_ERROR. Check logs", status_code=500)

def validate_request_data(req_body):
    """ Validate JSON request data """
    required_fields = ["schema", "required_ch_opps_flag", "replicate_lkp_stages_new", "explicit_execution"]
    
    ## Check if all required fields exist
    for field in required_fields:
        if field not in req_body:
            return f"Missing required field: {field}", False
    
    ## Validate data types
    if not isinstance(req_body["schema"], str):
        return "Invalid data type: 'schema' must be a string", False
    if not all(isinstance(req_body[field], bool) for field in required_fields if field != "schema"):
        return "Invalid data type: All fields except 'schema' must be boolean", False
    
    ## return successful validation
    return "Validation successful", True