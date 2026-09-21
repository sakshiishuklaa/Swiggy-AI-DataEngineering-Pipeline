
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        order_status as value_field,
        count(*) as n_records

    from SWIGGY.marts.fct_orders
    group by order_status

)

select *
from all_values
where value_field not in (
    'Delivered','Cancelled','Refunded'
)



  
  
      
    ) dbt_internal_test