#include "test_utils_common.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <string>
#include <vector>

#include "dbconnector.h"
#include "notificationconsumer.h"
#include "redis_utils.h"
#include "select.h"
#include "selectableevent.h"
#include "stateverification.h"
#include "table.h"
#include "timestamp.h"
#include "warm_restart.h"

namespace rebootbackend {

void TestUtils::wait_for_finish(swss::Select &s,
                                swss::SelectableEvent &finished,
                                long timeout_seconds) {
  swss::Selectable *sel;
  int ret;

  ret = s.select(&sel, timeout_seconds * 1000);
  EXPECT_EQ(ret, swss::Select::OBJECT);
  EXPECT_EQ(sel, &finished);
}

void TestUtils::populate_restart_table_state(swss::DBConnector &db,
                                             const std::string &app_name,
                                             const std::string &state) {
  swss::Table warmRestartTable(&db, STATE_WARM_RESTART_TABLE_NAME);
  warmRestartTable.hset(app_name, "state", state);
}

void TestUtils::check_warmboot_enabled(swss::DBConnector &db,
                                       bool expected_state) {
  swss::Table warmRestartTable(&db, STATE_WARM_RESTART_ENABLE_TABLE_NAME);
  std::string actual_state;
  warmRestartTable.hget("system", "enable", actual_state);
  EXPECT_EQ(actual_state, expected_state ? "true" : "false");
}

}  // namespace rebootbackend
