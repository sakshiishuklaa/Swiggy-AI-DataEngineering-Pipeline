-- back compat for old kwarg name
  
  begin;
    
        
            
            
            
            
        
    

    

    merge into SWIGGY.marts.fact_order_items as DBT_INTERNAL_DEST
        using SWIGGY.marts.fact_order_items__dbt_tmp as DBT_INTERNAL_SOURCE
        on ((DBT_INTERNAL_SOURCE.order_item_id = DBT_INTERNAL_DEST.order_item_id))

    
    when matched then update set
        "ORDER_ITEM_ID" = DBT_INTERNAL_SOURCE."ORDER_ITEM_ID","ORDER_ID" = DBT_INTERNAL_SOURCE."ORDER_ID","RESTAURANT_ID" = DBT_INTERNAL_SOURCE."RESTAURANT_ID","F_ID" = DBT_INTERNAL_SOURCE."F_ID","ORDER_TS" = DBT_INTERNAL_SOURCE."ORDER_TS","ORDER_DATE" = DBT_INTERNAL_SOURCE."ORDER_DATE","CITY" = DBT_INTERNAL_SOURCE."CITY","PRICE" = DBT_INTERNAL_SOURCE."PRICE","QUANTITY" = DBT_INTERNAL_SOURCE."QUANTITY","LINE_AMOUNT" = DBT_INTERNAL_SOURCE."LINE_AMOUNT"
    

    when not matched then insert
        ("ORDER_ITEM_ID", "ORDER_ID", "RESTAURANT_ID", "F_ID", "ORDER_TS", "ORDER_DATE", "CITY", "PRICE", "QUANTITY", "LINE_AMOUNT")
    values
        ("ORDER_ITEM_ID", "ORDER_ID", "RESTAURANT_ID", "F_ID", "ORDER_TS", "ORDER_DATE", "CITY", "PRICE", "QUANTITY", "LINE_AMOUNT")

;
    commit;