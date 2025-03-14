#!/usr/bin/env bash
#TODO - Remove dead branches
if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters"
    echo "Usage : $0 [URI of MongoDB Atlas, AWS Document DB, or Azure Cosmos DB] [Version to test, either 5.0, 5.1, 5.2, or 6.0]"
    exit 1
fi
if [[ $2 != "5.0" ]] && [[ $2 != "5.1" ]] && [[ $2 != "5.2" ]] && [[ $2 != "6.0" ]]; then
    echo "Invalid version; must be 5.0, 5.1, 5.2, or 6.0. Please use the pre-5.0 directory for running older versions."
fi

URI=$1
VERSION=$2
LOCAL_RESULTS_DIR="$(pwd)/results-${VERSION}"
IMAGE="mongo/mongodb-tests:${VERSION}"
rm -rf ${LOCAL_RESULTS_DIR}
mkdir ${LOCAL_RESULTS_DIR}

echo "results in : ${LOCAL_RESULTS_DIR}"

# echo "Starting test suite - Decimal"
# docker run --name mongodb-tests-decimal-${VERSION} -e "URI=${URI}" -v ${LOCAL_RESULTS_DIR}:/results ${IMAGE} decimal > /dev/null
# docker logs --follow mongodb-tests-decimal-${VERSION} > stdout_decimal.log
# docker cp mongodb-tests-decimal-${VERSION}:/results/. ${LOCAL_RESULTS_DIR}
# docker rm -v mongodb-tests-decimal-${VERSION}
# cp stdout_decimal.log ${LOCAL_RESULTS_DIR}/stdout_decimal.log
# echo "Decimal tests complete"

# echo "Starting test suite - Core"
# docker run --name mongodb-tests-core-${VERSION} -e "URI=${URI}" -v ${LOCAL_RESULTS_DIR}:/results ${IMAGE} core > /dev/null
# docker logs --follow mongodb-tests-core-${VERSION} > stdout_core.log
# docker cp mongodb-tests-core-${VERSION}:/results/. ${LOCAL_RESULTS_DIR}
# docker rm -v mongodb-tests-core-${VERSION}
# cp stdout_core.log ${LOCAL_RESULTS_DIR}/stdout_core.log
# echo "Core tests complete"

echo "Starting test suite - Transactions"
docker run --name mongodb-tests-core-txns-${VERSION} -e "URI=${URI}" -v ${LOCAL_RESULTS_DIR}:/results ${IMAGE} core_txns > /dev/null
docker logs --follow mongodb-tests-core-txns-${VERSION} > stdout_core_txns.log
docker cp mongodb-tests-core-txns-${VERSION}:/results/. ${LOCAL_RESULTS_DIR}
docker rm -v mongodb-tests-core-txns-${VERSION}
cp stdout_core_txns.log ${LOCAL_RESULTS_DIR}/stdout_core_txns.log
echo "Transactions tests complete"

# echo "Starting test suite - JSON Schema"
# docker run --name mongodb-tests-json-schema-${VERSION} -e "URI=${URI}" -v ${LOCAL_RESULTS_DIR}:/results ${IMAGE} json_schema > /dev/null
# docker logs --follow mongodb-tests-json-schema-${VERSION} > stdout_json_schema.log
# docker cp mongodb-tests-json-schema-${VERSION}:/results/. ${LOCAL_RESULTS_DIR}
# docker rm -v mongodb-tests-json-schema-${VERSION}
# cp stdout_json_schema.log ${LOCAL_RESULTS_DIR}/stdout_json_schema.log
# echo "JSON Schema tests complete"

# echo "Starting test suite - Change Streams"
# docker run --name mongodb-tests-change-streams-${VERSION} -e "URI=${URI}" -v ${LOCAL_RESULTS_DIR}:/results ${IMAGE} change_streams > /dev/null
# docker logs --follow mongodb-tests-change-streams-${VERSION} > stdout_change_streams.log
# docker cp mongodb-tests-change-streams-${VERSION}:/results/. ${LOCAL_RESULTS_DIR}
# docker rm -v mongodb-tests-change-streams-${VERSION}
# cp stdout_change_streams.log ${LOCAL_RESULTS_DIR}/stdout_change_streams.log
# echo "Change Streams tests complete"

# echo "Starting test suite - Aggregation"
# docker run --name mongodb-tests-aggregation-${VERSION} -e "URI=${URI}" -v ${LOCAL_RESULTS_DIR}:/results ${IMAGE} aggregation > /dev/null
# docker logs --follow mongodb-tests-aggregation-${VERSION} > stdout_aggregation.log
# docker cp mongodb-tests-aggregation-${VERSION}:/results/. ${LOCAL_RESULTS_DIR}
# docker rm -v mongodb-tests-aggregation-${VERSION}
# cp stdout_aggregation.log ${LOCAL_RESULTS_DIR}/stdout_aggregation.log
# echo "Aggregation tests complete"

echo "All tests complete"
