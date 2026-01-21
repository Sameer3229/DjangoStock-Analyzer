def clean_number(value):
   
    if value is None or value == "":
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # 1. Basic Cleanup
        clean_val = value.replace(",", "").replace("%", "").strip()
        
        # 2. Negative Handling (Bracket style: "(500)")
        if "(" in clean_val and ")" in clean_val:
            clean_val = "-" + clean_val.replace("(", "").replace(")", "")
            
        try:
            return float(clean_val)
        except ValueError:
            return 0.0
            
    return 0.0