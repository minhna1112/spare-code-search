(class_definition
  name: (identifier) @class.name) @class.declaration

(function_definition
  name: (identifier) @function.name) @function.declaration

(call
  function: [
      (identifier) @function.name
      (attribute
        (identifier) @function.name) @navigation_expression.name
  ]) @reference.definition


(parameters ) @parameter.declaration
(argument_list) @argument.declaration

