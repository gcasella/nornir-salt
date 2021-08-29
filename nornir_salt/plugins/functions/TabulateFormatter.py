"""
TabulateFormatter function
##########################

Function to transform results in a text table format using Tabulate module.

TabulateFormatter works with a list of dictionaries to represent them as a table,
if Nornir AggregatedResult object passed on to TabulateFormatter it uses 
ResultSerializer function to serialize results into a list of dictionaries.

Dependencies:

* Nornir 3.0 and beyond
* `Tabulate module <https://pypi.org/project/tabulate/>`_ for results table formatting

Sample code to use TabulateFormatter::

    from nornir import InitNornir
    from nornir_salt import TabulateFormatter
    from nornir_netmiko import netmiko_send_command

    nr = InitNornir(config_file="config.yaml")

    result = NornirObj.run(
        task=netmiko_send_command,
        command_string="show clock"
    )

    print(TabulateFormatter(result))
    # prints:
    # result                    changed    diff    failed    name          connection_retry    task_retry  exception    host
    # ------------------------  ---------  ------  --------  ----------  ------------------  ------------  -----------  ------
    # Sun Jul 11 08:41:06 2021  False              False     show clock                   0             0               ceos1
    # Timezone: UTC
    # Clock source: local
    # Sun Jul 11 08:41:06 2021  False              False     show clock                   0             0               ceos2
    # Timezone: UTC
    # Clock source: local
   
Reference
=========

.. autofunction:: nornir_salt.plugins.functions.TabulateFormatter.TabulateFormatter
"""
import logging
import traceback
from nornir.core.task import AggregatedResult
from .ResultSerializer import ResultSerializer

log = logging.getLogger(__name__)

try:
    import tabulate as tabulate_lib

    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    log.error("Failed to import tabulate library, install it: pip install tabulate")


def TabulateFormatter(result, tabulate=True, headers="keys", headers_exclude=[]):
    """
    Function to format results in a text table.

    :param result: list of dictionaries or ``nornir.core.task.AggregatedResult`` object
    :param tabulate: (dict or str or bool) controls tabulate behaviour
    :param headers: (list or str) list of table headers, comma-separated string of headers or
        one of tabulate supported values, e.g. ``keys``
    :param headers_exclude: (list) list of table headers, comma-separated string of headers
        to exclude

    Supported values for ``tabulate`` attribute:

    * ``brief`` - uses ``tablefmt`` is ``grid``, ``showindex`` is ``True`` 
        and ``headers`` set to ``host, name, result, exception``
    * ``True`` - uses ``headers``, no other formatting
    * ``False`` - does nothing, returns original results
    * ``extend`` - if result is a list, extends it to form final table, appends it as is otherwise
    * ``dictionary`` - dictionary value passed as ``**kwargs`` to ``tabulate.tabulate`` method
    """
    if not HAS_TABULATE:
        log.error(
            "nornir-salt:TabulateFormatter failed import tabulate library, install: pip install tabulate"
        )
        return result

    # decide on results to tabulate
    if isinstance(result, AggregatedResult):
        result_to_tabulate = ResultSerializer(result, add_details=True, to_dict=False)
    elif isinstance(result, list):
        result_to_tabulate = result
    else:
        log.error(
            "nornir-salt:TabulateFormatter unsupported results type '{}', supported - list or AggregatedResult".format(
                type(result)
            )
        )
        return result

    # check headers
    if isinstance(headers, str) and "," in headers:
        headers = [i.strip() for i in headers.split(",")]
    if isinstance(headers_exclude, str) and "," in headers_exclude:
        headers_exclude = [i.strip() for i in headers_exclude.split(",")]
        
    # form tabulate parameters and results
    if tabulate == "brief":
        tabulate = {
            "tablefmt": "grid",
            "showindex": True,
            "headers": ["host", "name", "result", "exception"],
        }
    elif tabulate == True:
        tabulate = {"headers": headers}
    elif tabulate == "extend":
        table_ = []
        tabulate = {"headers": headers}
        for res in result_to_tabulate:
            if isinstance(res["result"], list):
                table_.extend(
                    [
                        {**res, **i} if isinstance(i, dict) else {**res, "result": i}
                        for i in res.pop("result")
                    ]
                )
            else:
                table_.append(res)
        result_to_tabulate = table_
    elif isinstance(tabulate, dict):
        tabulate.setdefault("headers", headers)
    elif tabulate == False:
        return result        
    else:
        log.error(
            "nornir-salt:TabulateFormatter unsupported tabulate argument type '{}', supported - 'brief', bool, dict".format(
                type(tabulate)
            )
        )
        return result

    # filter result table if requested to do so
    if headers_exclude:
        result_to_tabulate = [
            {k: v for k, v in res.items() if k not in headers_exclude}
            for res in result_to_tabulate
        ]        
        
    # transform result_to_tabulate to list of lists
    if isinstance(tabulate["headers"], list):
        result_to_tabulate = [
            [item.get(i, "") for i in tabulate["headers"]]
            for item in result_to_tabulate
        ]

    return tabulate_lib.tabulate(result_to_tabulate, **tabulate)
