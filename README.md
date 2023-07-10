# inlinecalc
Inline Calculator, an Xed Plugin in Python  

In any Xed document or text you can simply type an expression and press CTRL+ENTER on the same line to calculate it.  

Example:  
> 1 + 2 * (sin(rad(45)) - 1.25)  
> = -0.08578641  

To use the plugin, place the src files into '/usr/lib/.../xed/plugins/' or something similar.

# How it works
inlinecalc breaks the input text into tokens and check for validity.  
It also builds an abstract syntax tree while parsing and then it interprets by walking to the bottom in LR order and bubbles the results of each computation to the parent node.  
The final node (root) will either hold a result or nothing at all.  

    * input : "1 + 2 * (sin(rad(45)) - 1.25)"  

    * tokens: '1', '+', '2', '*', '(', 'sin', '(', 'rad', '45', ')', ')', '-', '1.25', ')'

    * ast   :  
             (+)                       bop  
             / \                      /  \  
            1  (*)                  num  bop
               / \                      /  \
              2  (-)                  num   bop
                 / \                       /  \
             [sin]  1.25                 fun  num
              /                          /
          [rad]                        fun
            /                          /
          45                         num

# Code format note
It looks really poorly formatted on github.  
I personally use tabs with 4-space width indentation and github uses 8-space for some reason.  
