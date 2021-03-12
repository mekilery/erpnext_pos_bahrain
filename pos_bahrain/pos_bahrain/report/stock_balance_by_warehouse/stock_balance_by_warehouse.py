# Copyright (c) 2013, 	9t9it and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from toolz import merge, concat, compose
from functools import partial

warehouse_cols = [
    "opening_qty",
    "opening_val",
    "in_qty",
    "in_val",
    "out_qty",
    "out_val",
    "bal_qty",
    "bal_val",
    "val_rate",
    "reorder_level",
    "reorder_qty",
]


def execute(filters=None):
    from erpnext.stock.report.stock_balance.stock_balance import execute

    columns, data = execute(filters)

    warehouses = frappe.get_all(
        "Warehouse",
        filters={"is_group": 0, "disabled": 0},
        fields=["name", "warehouse_name"],
    )
    warehouse_data = {
        x.get("name"): x.get("warehouse_name").strip().lower().replace(" ", "_")
        for x in warehouses
    }

    return _get_columns(columns, warehouse_data), _get_data(
        data, columns, warehouse_data
    )


def _get_columns(columns, warehouses):
    existing_columns = [x for x in columns if x.get("fieldname") in warehouse_cols]

    columns_by_warehouse = list(
        concat(
            [
                [
                    merge(
                        y,
                        {
                            "fieldname": "_".join([y.get("fieldname"), v]),
                            "label": " - ".join([y.get("label"), k]),
                        },
                    )
                    for y in existing_columns
                ]
                for k, v in warehouses.items()
            ]
        )
    )

    return list(
        concat(
            [
                filter(
                    lambda x: x.get("fieldname") not in warehouse_cols,
                    columns,
                ),
                columns_by_warehouse,
            ]
        )
    )


def _get_data(data, columns, warehouses):
    def fix_data(row):  # dict-ify existing data
        row_iter = iter(row)
        return {x: next(row_iter) for x in column_fieldnames}

    def make_col(warehouse_col, x):
        return "_".join(
            [
                warehouse_col,
                warehouses.get(x.get("warehouse")),
            ]
        )

    column_fieldnames = list(map(lambda x: x.get("fieldname"), columns))

    by_warehouse_cols = partial(
        map,
        lambda x: merge(x, {make_col(col, x): x.get(col) for col in warehouse_cols}),
    )

    make_data = compose(
        list,
        by_warehouse_cols,
        partial(map, fix_data),
        lambda: data,
    )

    return make_data()
