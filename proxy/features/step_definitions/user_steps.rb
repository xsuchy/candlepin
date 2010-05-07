require 'spec/expectations'
require 'candlepin_api'

Given /^an owner admin "([^\"]*)"$/ do |username|
    @username = username
    @password = 'password'
    @candlepin.create_user(@test_owner['id'], @username, @password)
end

Given /^I am logged in as "([^\"]*)"$/ do |username|
    @owner_admin_cp = connect(username=username, password="password")
end