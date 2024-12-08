# From https://stackoverflow.com/a/23816211
from sources import SourceResult


def format_request(req, headers=False):
    if headers:
        return '{}\n{}\r\n{}\r\n\r\n{}\n{}'.format(
            '-----------START-----------',
            req.method + ' ' + req.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
            '------------END------------',
        )
    else:
        return '{}\n{}\r\n{}\n{}'.format(
            '-----------START-----------',
            req.method + ' ' + req.url,
            req.body,
            '------------END------------',
        )


def format_iprecords(ipRecord: dict[str, SourceResult]):
    ret = ""
    for source, recordData in ipRecord.items():
        ret += '{}{}{}\n{}\n{}{}{}\n'.format(
            '-----------',
            source,
            '-----------',
            '\n'.join(
                recordData.ips) if recordData.status else "FAILED TO UPDATE",
            '-----------',
            source,
            '-----------',
        )
    return ret
