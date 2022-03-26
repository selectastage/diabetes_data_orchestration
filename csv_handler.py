import boto3
import pandas as pd
import boto3
import sys

if sys.version_info[0] < 3: 
    from StringIO import StringIO # Python 2.x
else:
    from io import StringIO # Python 3.x
    
aws_access_key_id='ASIARPLJXAZNTWQWBFUT'
aws_secret_access_key= 'PUT7n9bI2/7wr72IeyoqjEUONylsFGo6fLQWbRKZ'
aws_session_token= 'FwoGZXIvYXdzEOL//////////wEaDH/W8FATz/rDimhR7SK/AXSMJrDcwKutwcc6PcXHduR2gI7xjS1nfTZvECZFlbL4vEVEhgI3OB+ar3uKa5nCwv3LdAEj1aNx1rrGLjQJAQQOlOde3hq7OdlqTij5qZLf2+G4c5HIc+FCskAdRKEYSZauPcHCb6L1gfG6TUWaO9nEyKrhmh525gaSbnU68zWDyW+Tldbp69pFgUpn0APX6tbBMDFvUQn31CDHN0lXa9z8KHlWyEDyrUrlzGL6/gO3gWDotLAPJOfMSohhoHIRKIzS8JEGMi3F9rUr29BhecynXx6NXGEujC9AcjaRWgVvq0xPoL4M272ackkKuODppIDiWFQ='


s3 = boto3.resource('s3',
                    aws_access_key_id= aws_access_key_id,
                    aws_secret_access_key= aws_secret_access_key ,
                    aws_session_token= aws_session_token)

s3_client = boto3.client('s3',aws_access_key_id= aws_access_key_id,
                    aws_secret_access_key= aws_secret_access_key ,
                    aws_session_token= aws_session_token)


s3_bucket_name ='bucketeble'
my_bucket =s3.Bucket(s3_bucket_name) 

keys = [my_bucket_object.key for my_bucket_object in my_bucket.objects.all()]
objects = [s3_client.get_object(Bucket= s3_bucket_name, Key=key) for key in keys]


def lambda_handler():
    
    body = objects[0]['Body']

    df_1 = pd.read_csv(StringIO(body.read().decode('utf-8')))
    
    
if __name__ == 'main':
    lambda_handler()