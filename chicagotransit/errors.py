def error_handler(exception):
    if exception == 'Invalid API access key supplied':
        raise InvalidKeyException
    elif exception == 'No data found for parameter':
        raise NoDataFoundException
    else:
        raise Exception(exception)


class InvalidKeyException(Exception):
    pass


class NoDataFoundException(Exception):
    pass


class InvalidLineException(Exception):
    pass
