import argparse
import fnmatch
import json
import logging.config
import os
import re
from datetime import date

# hardcoded right now
logging.config.fileConfig('logging.conf')

# list of suites run by the docker container
SUITES = ['aggregation', 'change_streams', 'core', 'decimal', 'core_txns', 'json_schema']

def parse_args():
    """
    parse arguments from command line

    :return: list of arguments
    """
    parser = argparse.ArgumentParser(description='MongoDB correctness analysis program')

    parser.add_argument(
        '--platform',
        type=str,
        action='store',
        required=True,
        help='platform for results, i.e.: atlas, documentdb, foundationdb, cosmos, etc.'
    )

    parser.add_argument(
        '--version',
        type=str,
        action='store',
        required=False,
        default='v5.0',
        help='version test suite was run against'
    )

    parser.add_argument(
        '--previewFeatures',
        type=str,
        action='store',
        required=True,
        default='v5.0',
        help='comma seperated list of PreviewFeatures enabled on the account'
    )

    parser.add_argument(
        '--rdir',
        type=str,
        action='store',
        required=False,
        default='./results-5.0',
        help='directory where results are stored'
    )

    parser.add_argument(
        '--csv',
        type=str,
        action='store',
        required=False,
        default='./results.csv',
        help='csv file of processed results'
    )
    return parser.parse_args()

def get_tests_list(suite, platform, version, results_dir):
    """
    simply get a list of the tests enriched with data about the run

    :param suite:
    :param platform:
    :param version:
    :param results_dir:
    :return:
    """
    logger.debug('attempt to process json file')
    json_f = '{}/{}'.format(
        results_dir,
        fnmatch.filter(os.listdir(results_dir), '*{}.json'.format(suite))[0]
    )
    with open(json_f, 'r') as f:
        tests = json.load(f)
    for result in tests['results']:
        result['suite'] = suite
        result['platform'] = platform
        result['version'] = version
        result['processed'] = False
    return tests['results']

def get_log_lines_as_dict(suite, results_dir):
    """
    all correctness test run output has [CATEGORY:TEST] at the start of the line
    simply read the log file get the output lines for the given test add it to a
    dictionary key. {TEST: [line, line...]}

    :param suite:
    :param results_dir:
    :return:
    """
    logger.debug('attempt to process log lines')

    pattern = re.compile(r'^\[js_test:(.*?)\].*')
    if suite == 'json_schema':
        pattern = re.compile(r'^\[json_schema_test:(.*?)\].*')

    log_f = '{}/{}'.format(
        results_dir,
        fnmatch.filter(os.listdir(results_dir), '*{}.log'.format(suite))[0]
    )
    logger.debug('LOGF {}'.format(log_f))
    # build dictionary where key is test name
    log_lines = {}
    with open(log_f) as log_file:
        test = ''
        for line in log_file:
            match = pattern.match(line)
            if match:
                current_test = match.group(1)
                if current_test != test:
                    logger.debug('old test:{}, current test:{}'.format(test, current_test))
                    test = current_test
                    log_lines[test] = []
                log_lines[test].append(line[:5000].strip())
            else:
                logger.debug('skipping line: {}'.format(line.strip()))
    logger.info('{}:number of test:{}'.format(suite, len(log_lines.keys())))
    return log_lines

def add_logs_lines_to_results(test_list, log_dict):
    """
    for  each of the tests add the logs to the test

    :param test_list:
    :param log_dict:
    :return:
    """
    logger.debug('merging results')
    for test in test_list:
        # covers test file ending in js or json
        key = re.match(r'^.*/(.*)\.js.*', test['test_file'])
        if key and key.group(1) in log_dict:
            test_name = key.group(1)
            test['log_lines'] = log_dict[test_name]
        else:
            logger.warning('key {} not in log'.format(key))

def extract_error(regex_for_match, regex_for_extract, log_lines):
    newlist = list(filter(regex_for_match.search, log_lines))
    newlist = [''.join(re.findall(regex_for_extract,s)) for s in newlist]
    dislist = list(set(newlist))
    if len(dislist) == 1:
        return dislist[0]
    else:
        return dislist

def process_failures(test_list):
    """
    for  each of the tests, try to extract the first error

    :param test_list:
    :return:
    """
    logger.debug('extracting errors')
    errorMsg = re.compile(r'\"errmsg\"')
    uncaughtException = re.compile(r'uncaught exception')
    for test in test_list:
        # covers test file ending in js or json
        if 'log_lines' in test and test['status'] != "pass":
            err_list = extract_error(errorMsg, r'errmsg\" : (.*)', test['log_lines'])
            if len(err_list) == 0:
                err_list = extract_error(uncaughtException, r'uncaught exception: (.*)', test['log_lines'])
            
            # if len(err_list) == 0 and test['status'] == "fail":                
            #    breakpoint()
            test['errmsg'] = err_list[:1000]

def main():
    """

    :return:
    """
    logger.debug('starting analysis')
    today = date.today()
    args = parse_args()

    try:
        
        logger.debug('attempting to process results for {}'.format(args.platform))
        suites = None
        suites = SUITES

        with open(args.csv, 'w+') as out:
            out.write('date,test file,suite,platform,version,status,preview features,errmsg\n')
            for suite in suites:
                test_results = get_tests_list(suite, args.platform, args.version, args.rdir)
                log_lines = get_log_lines_as_dict(suite, args.rdir)
                add_logs_lines_to_results(test_results, log_lines)
                process_failures(test_results)
                for result in test_results:
                    tn = result['test_file']
                    s = result['suite']
                    p = result['platform']
                    v = result['version']                   
                    r = result['status']
                    err = result['errmsg'] if 'errmsg' in result else ''
                    if type(err) is list:
                        err = list(map(lambda x: x.replace('"','""'), err))
                    else:
                        err = err.replace('"','""')
                    out.write('{},{},{},{},{},{},{},"{}"\n'.format(today, tn, s, p, v, r, args.previewFeatures, err))

        logger.info('finished analysis, csv file created: {}'.format(args.csv))
    except Exception as e:
        # general exception in case connection/inserts/finds/updates fail.
        logger.error('exception occurred during analysis: {}'.format(e), exc_info=True)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    main()