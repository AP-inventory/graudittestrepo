import os
import boto3
import datetime

success_result = "success"
failure_result = "failed"


def validate_aws_credentials(access_key_id, secret_access_key):
    if not access_key_id or not secret_access_key:
        return False
    try:
        ec2_client = boto3.client('ec2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
        response = ec2_client.describe_instances()
        return success_result, "AWS credentials are valid"
    except Exception as e:
        return failure_result, "AWS credentials are invalid"


def create_instance_ami(instance_id, reboot_user_choice, access_key_id, secret_access_key):
    try:
        ec2_client = boto3.client('ec2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)

        instance_ids = [instance_id]
        instances = ec2_client.describe_instances(InstanceIds=instance_ids)
        if not instances['Reservations']:
            return failure_result, f"Instance with ID '{instance_id}' does not exist."

        #instance_info = instances['Reservations'][0]['Instances'][0]
        timestamp = datetime.datetime.now().strftime("%Y/%m/%d-%H/%M")

        print(reboot_user_choice.lower())
        if reboot_user_choice.lower() == 'yes':
            print(f"Stopping instance {instance_id}...")
            ec2_client.stop_instances(InstanceIds=instance_ids)
            waiter = ec2_client.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=instance_ids)
            
            ami_response = ec2_client.create_image(
            InstanceId=instance_id,
            Name=f"AMI-{instance_id}-{timestamp}",
            Description=f"AMI created for instance {instance_id}",
            Encrypted=True,
            NoReboot=True  # You can change this if you want to reboot the instance
            )
            
            print(f"Starting instance {instance_id}...")
            ec2_client.start_instances(InstanceIds=instance_ids)
            waiter = ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=instance_ids)
            
            return success_result, f"AMI creation initiated for instance {instance_id}, AMI ID: {ami_response['ImageId']}, please check AWS CONSOLE AMI FOR STATUS as it may take some time to complete the AMI"
    
        else:
    
            ami_response = ec2_client.create_image(
                InstanceId=instance_id,
                Name=f"AMI -{instance_id}-{timestamp}",
                Description=f"AMI created for instance {instance_id}",
                Encrypted=True,
                NoReboot=True 
            )


            return success_result, f"AMI creation initiated for instance {instance_id}, AMI ID: {ami_response['ImageId']}, please check AWS CONSOLE AMI FOR STATUS as it may take some time to complete the AMI"

    except Exception as e:
        if "Invalid id" or "InvalidInstanceID" in str(e):
            return failure_result, f"Invalid instance ID '{instance_id}', instance does not exist"
        else:
            return failure_result, f"Error occurred: Please verify access to the account or provide correct input details"


def aws_lm_py_instance_ami():
    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    #reboot_user_choice = "YES"   #WARNING: Instances will be rebooted, providede instances will stopped then ami will be initiad then instance will be started.
    reboot_user_choice = "no"   #AMI will be intiated without instnace reboot but this is not recommended since it can lead to data inconsistencies in the AMI
    
    
    instance_ids_input = "i-0eb57058606d19356,i-029bc4e99d848fe13"
    instance_ids = instance_ids_input.replace(" ", "").split(",")



    if not instance_ids_input:
        return failure_result, "Please provide instance IDs."

    if not access_key_id or not secret_access_key:
        return failure_result, "Please provide AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
    
    if not reboot_user_choice: 
        return failure_result, "Please select either one entity YES OR NO."
    
    
    status, message = validate_aws_credentials(access_key_id, secret_access_key)
    if status == failure_result:
        return failure_result, message

    success_messages = []
    failure_messages = []

    for instance_id in instance_ids:
        status, message = create_instance_ami(instance_id, reboot_user_choice, access_key_id, secret_access_key)
        if status == success_result:
            success_messages.append(message)
        else:
            failure_messages.append(message)

    success_message = "\n".join(success_messages)
    failure_message = "\n".join(failure_messages)

    if success_message and failure_message:
        return success_result, success_message + "\n" + failure_message
    elif success_message:
        return success_result, success_message
    elif failure_message:
        return failure_result, failure_message
    else:
        return failure_result, "No AMI creation processed."




if __name__ == "__main__":
    status, message = aws_lm_py_instance_ami()
    print("Status:", status)
    print("Message:", message)
