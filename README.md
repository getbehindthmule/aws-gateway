# aws-gateway

1. Create Lambda and deploy via SAM / Intellij
2. Use aws cli / groovy script to set / update versions and labels

    aws lambda publish-version --function-name arn:aws:lambda:eu-west-1:382959638855:function:lowercase-lambda

    aws lambda get-function-configuration --function-name arn:aws:lambda:eu-west-1:382959638855:function:lowercase-lambda

    aws lambda list-versions-by-function --function-name arn:aws:lambda:eu-west-1:382959638855:function:lowercase-lambda

    aws lambda create-alias --function-name arn:aws:lambda:eu-west-1:382959638855:function:lowercase-lambda --function-version 1 --name DEV

    aws lambda update-alias --function-name arn:aws:lambda:eu-west-1:382959638855:function:lowercase-lambda --function-version 2 --name DEV

    aws lambda create-alias --function-name arn:aws:lambda:eu-west-1:382959638855:function:lowercase-lambda --function-version 1 --name PROD

    aws lambda list-functions

3. Use troposphere to configure apigateway

    aws lambda add-permission --function-name arn:aws:lambda:eu-west-1:382959638855:function:lowercase-lambda --source-arn arn:aws:execute-api:eu-west-1:382959638855:gxncimsb17/*/POST/uppercase --principal apigateway.amazonaws.com --statement-id apigateway-access --action lambda:InvokeFunction


**Cannot use versions / labels above because each stack creation creates an entirely new Lambda Function definition (pointing to the existing lambda zip in the S3 bucket). Therefore setting alias' or versions on an existing lambda definition has no effect.**

**Proposal:**

a separate S3 bucket per 'stage', promoting zip files to the next stage via build
a separate stack definition per 'stage' (and so separate troposphere definition, referring to different S bucket)

There will be a separate dynamodb per 'stage'. Here is a reminder of the command to add test data to the DB
aws dynamodb put-item --table-name DevCompanyTable --item file://item.json
