import logging
import re
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def pytest_addoption(parser):
    group = parser.getgroup('terminal reporting')
    group.addoption(
        '--prometheus-pushgateway-url',
        help='Push Gateway URL to send metrics to'
    )
    group.addoption(
        '--prometheus-metric-prefix',
        help='Prefix for all prometheus metrics'
    )
    group.addoption(
        '--prometheus-extra-label',
        action='append',
        help='Extra labels to attach to reported metrics'
    )
    group.addoption(
        '--prometheus-job-name',
        help='Value for the "job" key in exported metrics'
    )

def pytest_configure(config):
    if config.getoption('prometheus_pushgateway_url') and config.getoption('prometheus_metric_prefix'):
        config._prometheus = PrometheusReport(config)
        config.pluginmanager.register(config._prometheus)

def pytest_unconfigure(config):
    prometheus = getattr(config, '_prometheus', None)

    if prometheus:
        del config._prometheus
        config.pluginmanager.unregister(prometheus)


class PrometheusReport:
    def __init__(self, config):
        self.config = config
        self.prefix = config.getoption('prometheus_metric_prefix')
        self.pushgateway_url = config.getoption('prometheus_pushgateway_url')
        self.job_name = config.getoption('prometheus_job_name')
        self.registry = CollectorRegistry()

        self.passed = []
        self.failed = []
        self.skipped = []

        self.extra_labels = {item[0]: item[1] for item in [i.split('=', 1) for i in config.getoption('prometheus_extra_label')]}

    def _make_metric_name(self, name):
        unsanitized_name = '{prefix}{name}'.format(
                prefix=self.prefix,
                name=name
        )
        # Valid names can only contain these characters, replace all others with _
        # https://prometheus.io/docs/concepts/data_model/#metric-names-and-labels
        pattern = r'[^a-zA-Z0-9_]'
        replacement = '_'
        return re.sub(pattern, replacement, unsanitized_name)

    def _make_labels(self, testname):
        ret = self.extra_labels.copy()
        ret["testname"] = testname
        return ret

    def _get_label_names(self):
        return self._make_labels("").keys()

    def add_metrics_for_tests(self, metric, testnames):
        for testname in testnames:
            labels = self._make_labels(testname)
            metric.labels(**labels).inc()


    def pytest_runtest_logreport(self, report):
        # https://docs.pytest.org/en/latest/reference.html#_pytest.runner.TestReport.when
        # 'call' is the phase when the test is being ran
        if report.when == 'call':

            funcname = report.location[2]
            name = self._make_metric_name(funcname)

            if report.outcome == 'passed':
                self.passed.append(name)
            elif report.outcome == 'skipped':
                self.skipped.append(name)
            elif report.outcome == 'failed':
                self.failed.append(name)



    def pytest_sessionfinish(self, session):

        passed_metric = Gauge(self._make_metric_name("passed"),
                "Number of passed tests",
                labelnames=self._get_label_names(),
                registry=self.registry)
        self.add_metrics_for_tests(passed_metric, self.passed)


        failed_metric = Gauge(self._make_metric_name("failed"),
                "Number of failed tests",
                labelnames=self._get_label_names(),
                registry=self.registry)
        self.add_metrics_for_tests(failed_metric, self.failed)

        skipped_metric = Gauge(self._make_metric_name("skipped"),
                "Number of skipped tests",
                labelnames=self._get_label_names(),
                registry=self.registry)
        self.add_metrics_for_tests(skipped_metric, self.skipped)

        push_to_gateway(self.pushgateway_url, registry=self.registry, job=self.job_name)

    def pytest_terminal_summary(self, terminalreporter):
        # Write to the pytest terminal
        terminalreporter.write_sep('-',
                'Sending test results to Prometheus pushgateway at {url}'.format(
                    url=self.pushgateway_url))

