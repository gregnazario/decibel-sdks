package trade.decibel.sdk.bdd

import io.cucumber.junit.Cucumber
import io.cucumber.junit.CucumberOptions
import org.junit.runner.RunWith

/**
 * Cucumber test runner for BDD tests.
 */
@RunWith(Cucumber::class)
@CucumberOptions(
    features = ["../../../features"],
    glue = ["trade.decibel.sdk.bdd"],
    plugin = ["pretty", "html:target/cucumber-report.html"],
    tags = "@cucumber"
)
class CucumberTest
