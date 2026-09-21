
  
    

        create or replace transient table SWIGGY.marts.dim_food
         as
        (select f_id, food_name, veg_or_non_veg from SWIGGY.staging.stg_food
        );
      
  