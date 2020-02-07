from troposphere import Ref, Template, Output
from troposphere.apigateway import RestApi, Method
from troposphere.apigateway import Resource, MethodResponse
from troposphere.apigateway import Integration, IntegrationResponse
from troposphere.apigateway import Deployment, Stage, ApiStage
from troposphere.apigateway import UsagePlan, QuotaSettings, ThrottleSettings
from troposphere.apigateway import ApiKey, StageKey, UsagePlanKey
from troposphere.iam import Role, Policy
from troposphere.awslambda import Function, Code, Alias
from troposphere import GetAtt, Join


t = Template()

# Create the Api Gateway
rest_api = t.add_resource(RestApi(
    "IntTransformGatewayApi",
    Name="IntTransformGatewayApi"
))


# Create a role for the lambda function
t.add_resource(Role(
    "TransformGatewayLambdaExecutionRole",
    Path="/",
    Policies=[Policy(
        PolicyName="root",
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Action": ["logs:*"],
                "Resource": "arn:aws:logs:*:*:*",
                "Effect": "Allow"
            }, {
                "Action": ["lambda:*"],
                "Resource": "*",
                "Effect": "Allow"
            }]
        })],
    AssumeRolePolicyDocument={"Version": "2012-10-17", "Statement": [
        {
            "Action": ["sts:AssumeRole"],
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "lambda.amazonaws.com",
                    "apigateway.amazonaws.com"
                ]
            }
        }
    ]},
))

# Create the Lambda function
uppercase_function = t.add_resource(Function(
    "UppercaseFunction",
    Code=Code(
        S3Bucket="gs-serverless-store",
        S3Key="uppercase.zip"
    ),
    Handler="greenhills.Uppercase",
    Role=GetAtt("TransformGatewayLambdaExecutionRole", "Arn"),
    Runtime="java8",
))

lowercase_function = t.add_resource(Function(
    "LowercaseFunction",
    Code=Code(
        S3Bucket="gs-lambda-store",
        S3Key="lowercase-lambda.zip"
    ),
    Handler="greenhills.Lowercase",
    Role=GetAtt("TransformGatewayLambdaExecutionRole", "Arn"),
    Runtime="java8",
))

get_company_function = t.add_resource(Function(
    "GetCompanyFunction",
    Code=Code(
        S3Bucket="gs-lambda-store",
        S3Key="get-company.zip"
    ),
    Handler="greenhills.GetCompanyHandler",
    Role=GetAtt("TransformGatewayLambdaExecutionRole", "Arn"),
    Runtime="java8",
))

# Create a resource to map the lambda function to
uppercase_resource = t.add_resource(Resource(
    "UppercaseResource",
    RestApiId=Ref(rest_api),
    PathPart="uppercase",
    ParentId=GetAtt("IntTransformGatewayApi", "RootResourceId"),
))

# Create a Lambda API method for the Lambda resource
uppercase_method = t.add_resource(Method(
    "UppercaseLambdaMethod",
    DependsOn='UppercaseFunction',
    RestApiId=Ref(rest_api),
    AuthorizationType="NONE",
    ResourceId=Ref(uppercase_resource),
    HttpMethod="POST",
    Integration=Integration(
        Credentials=GetAtt("TransformGatewayLambdaExecutionRole", "Arn"),
        Type="AWS",
        IntegrationHttpMethod='POST',
        IntegrationResponses=[
            IntegrationResponse(
                StatusCode='200'
            )
        ],
        Uri=Join("", [
            "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/",
            GetAtt("UppercaseFunction", "Arn"),
            "/invocations"
        ])
    ),
    MethodResponses=[
        MethodResponse(
            "CatResponse",
            StatusCode='200'
        )
    ]
))

# Create a resource to map the lambda function to
lowercase_resource = t.add_resource(Resource(
    "LowercaseResource",
    RestApiId=Ref(rest_api),
    PathPart="lowercase",
    ParentId=GetAtt("IntTransformGatewayApi", "RootResourceId"),
))

# Create a Lambda API method for the Lambda resource
lowercase_method = t.add_resource(Method(
    "LowercaseLambdaMethod",
    DependsOn='LowercaseFunction',
    RestApiId=Ref(rest_api),
    AuthorizationType="NONE",
    ResourceId=Ref(lowercase_resource),
    HttpMethod="POST",
    Integration=Integration(
        Credentials=GetAtt("TransformGatewayLambdaExecutionRole", "Arn"),
        Type="AWS",
        IntegrationHttpMethod='POST',
        IntegrationResponses=[
            IntegrationResponse(
                StatusCode='200'
            )
        ],
        Uri=Join("", [
            "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/",
            GetAtt("LowercaseFunction", "Arn"),
            "/invocations"
        ])
    ),
    MethodResponses=[
        MethodResponse(
            "CatResponse",
            StatusCode='200'
        )
    ]
))

# Create a resource to map the lambda function to
get_company_resource = t.add_resource(Resource(
    "GetCompanyResource",
    RestApiId=Ref(rest_api),
    PathPart="company",
    ParentId=GetAtt("IntTransformGatewayApi", "RootResourceId"),
))

# Create a Lambda API method for the Lambda resource
get_company_method = t.add_resource(Method(
    "GetCompanyLambdaMethod",
    DependsOn='GetCompanyFunction',
    RestApiId=Ref(rest_api),
    AuthorizationType="NONE",
    ResourceId=Ref(get_company_resource),
    HttpMethod="GET",
    RequestParameters={"method.request.path.proxy": True, "method.request.querystring.id": True},
    Integration=Integration(
        Credentials=GetAtt("TransformGatewayLambdaExecutionRole", "Arn"),
        Type="AWS",
        IntegrationHttpMethod='POST',
        RequestTemplates={"application/json": "{\"id\": $input.params('id')}"},
        IntegrationResponses=[
            IntegrationResponse(
                StatusCode='200'
            )
        ],
        Uri=Join("", [
            "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/",
            GetAtt("GetCompanyFunction", "Arn"),
            "/invocations"
        ])
    ),
    MethodResponses=[
        MethodResponse(
            "CatResponse",
            StatusCode='200'
        )
    ]
))

# Create a deployment
stage_name = 'Int'

deployment = t.add_resource(Deployment(
    "%sDeployment" % stage_name,
    DependsOn=["UppercaseLambdaMethod", "LowercaseLambdaMethod"],
    RestApiId=Ref(rest_api),
))

stage = t.add_resource(Stage(
    '%sStage' % stage_name,
    StageName=stage_name,
    RestApiId=Ref(rest_api),
    DeploymentId=Ref(deployment)
))

key = t.add_resource(ApiKey(
    "ApiKey",
    StageKeys=[StageKey(
        RestApiId=Ref(rest_api),
        StageName=Ref(stage)
    )]
))

# Create an API usage plan
usagePlan = t.add_resource(UsagePlan(
    "ExampleUsagePlan",
    UsagePlanName="ExampleUsagePlan",
    Description="Example usage plan",
    Quota=QuotaSettings(
        Limit=50000,
        Period="MONTH"
    ),
    Throttle=ThrottleSettings(
        BurstLimit=500,
        RateLimit=5000
    ),
    ApiStages=[
        ApiStage(
            ApiId=Ref(rest_api),
            Stage=Ref(stage)
        )]
))

# tie the usage plan and key together
usagePlanKey = t.add_resource(UsagePlanKey(
    "ExampleUsagePlanKey",
    KeyId=Ref(key),
    KeyType="API_KEY",
    UsagePlanId=Ref(usagePlan)
))

# Add the deployment endpoint as an output
t.add_output([
    Output(
        "ApiEndpoint",
        Value=Join("", [
            "https://",
            Ref(rest_api),
            ".execute-api.eu-west-1.amazonaws.com/",
            stage_name
        ]),
        Description="Endpoint for this stage of the api"
    ),
    Output(
        "ApiKey",
        Value=Ref(key),
        Description="API key"
    ),
])


print(t.to_json())
