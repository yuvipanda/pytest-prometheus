# pytest Prometheus Reporter

A [pytest](https://docs.pytest.org/en/latest/) plugin that reports test results
to a [Prometheus PushGateway](https://github.com/prometheus/pushgateway).

## Installation

You can install it with pip:

```bash
pip install pytest-prometheus
```

It'll automatically register as a pytest plugin - no extra steps needed.

## Usage

When invoking `py.test`, provide the following arguments:

1. `--prometheus-pushgateway-url`

   URL to the pushgateway to send metrics to. Authentication is not supported.

2. `--prometheus-metric-prefix`

   Each metric exported will be prefixed with this.

3. `--prometheus-job-name`

   The value for the `job` label in the exported metrics. This is used as the
   grouping key, and should be explicitly specified.

3. `--prometheus-extra-label`

   This takes values of form `key=value`, and each metric will have these key
   value pairs as labels. Can be repeated many times.


As soon as a test is completed, a guage with value 0 or 1 is sent to the
pushgateway depending on wether it failed or passed. The name of the metric used
is `{prefix}{name_of_test_function}`, and the description contains the name of
the file as well.

So if you had a test named `test_website_up` and the
`--prometheus-metric-prefix` value was 'mywebsite_' then the metric name would
be `mywebsite_test_website_up`.

## Use case

It's nice to have complex tests (such as, 'is my website up and can I simulate
the entire login flow') that report their values to Prometheus. There is
currently no easy way to do
this - [black box exporter](https://github.com/prometheus/blackbox_exporter) is
too simplistic.

With this reporter, you can write your complex checks / tests as pytest tests,
and use this to collect metrics! This is much more maintainable long run than
ad-hoc python / bash scripts.

## Inspiration

[pytest-statsd](https://github.com/jlane9/pytest-statsd) was an inspiration for
this codebase!
