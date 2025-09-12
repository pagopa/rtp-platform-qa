import os
import time

import pymongo
from pymongo.errors import ConnectionFailure
from pymongo.errors import OperationFailure
from utilities import require_env

# --- Configuration ---
CONNECTION_STRING = require_env('COSMOS_DB_CONNECTION_STRING')
DATABASE_NAME = 'rtp'
COLLECTION_NAME = 'rtps'
BATCH_SIZE = 20
SECONDS_TO_SLEEP = 1
SERVICE_PROVIDER_DEBTOR = require_env('SERVICE_PROVIDER')

def delete_test_records_with_confirmation():
    """
    Connects to Cosmos DB, counts matching records, asks for user confirmation,
    and then deletes the records in batches if confirmed.
    """
    client = None
    total_deleted_count = 0

    try:
        # --- 1. Connect to the Database ---
        print('Attempting to connect to Cosmos DB...')
        client = pymongo.MongoClient(CONNECTION_STRING)
        client.admin.command('ping')
        print('Connection established successfully!')

        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        query_filter = {'serviceProviderDebtor': SERVICE_PROVIDER_DEBTOR}

        # --- 2. Count Records and Ask for Confirmation ---
        print('\n🔍 Searching for documents to delete...')

        # Use count_documents for an efficient count without fetching all the data
        document_count = collection.count_documents(query_filter)

        if document_count == 0:
            print('✅ No documents found with the specified criteria. Nothing to do.')
            return

        print(f"\nFound {document_count} documents matching the criteria.")

        # Ask for user confirmation before proceeding
        confirmation = input('Do you want to proceed with the deletion? (y/n): ').lower().strip()

        # --- 3. Proceed only if User Confirms ---
        if confirmation in ['y', 'yes']:
            print('\nUser confirmed. Starting deletion process...')

            # The batched deletion loop
            while total_deleted_count < document_count:
                # Find the _ids of a batch of documents
                documents_to_delete = list(collection.find(query_filter, {'_id': 1}).limit(BATCH_SIZE))

                if not documents_to_delete:
                    # This is a safeguard; the loop should naturally end.
                    break

                ids_to_delete = [doc['_id'] for doc in documents_to_delete]

                # Delete the current batch
                result = collection.delete_many({'_id': {'$in': ids_to_delete}})

                deleted_count = result.deleted_count
                total_deleted_count += deleted_count

                print(f"-> Deleted batch of {deleted_count} documents. Total so far: {total_deleted_count}.")

                # Sleep to avoid overwhelming the database
                time.sleep(SECONDS_TO_SLEEP)

            print(f"\n🎉 Operation completed! Total documents deleted: {total_deleted_count}.")

        else:
            # User cancelled the operation
            print('\n🛑 Operation cancelled by the user. No documents were deleted.')

    except ConnectionFailure as e:
        print(f"Connection Error: Could not connect to MongoDB. Details: {e}")
    except OperationFailure as e:
        print(f"An error occurred during a database operation: {e.details}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # --- 4. Close the Connection ---
        if client:
            client.close()
            print('Database connection closed.')


if __name__ == '__main__':
    delete_test_records_with_confirmation()
