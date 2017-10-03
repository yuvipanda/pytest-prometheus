from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, generate_latest

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

        self.extra_labels = {item[0]: item[1] for item in [i.split('=', 1) for i in config.getoption('prometheus_extra_label')]}
        print(self.extra_labels)

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            registry = CollectorRegistry()
            name = '{prefix}{funcname}'.format(
                prefix=self.prefix,
                funcname=report.location[2]
            )
            metric = Gauge(name, report.nodeid, self.extra_labels.keys(), registry=registry)
            metric.labels(**self.extra_labels).set(1 if report.outcome == 'passed' else 0)
            push_to_gateway(self.pushgateway_url, registry=registry, job=self.job_name)
