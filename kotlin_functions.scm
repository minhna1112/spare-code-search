;;; Function definitions

(function_declaration
	. (simple_identifier)) @function

(getter
	("get")) @function.builtin
(setter
	("set")) @function.builtin

(primary_constructor) @constructor
(secondary_constructor
	("constructor")) @constructor

(constructor_invocation
	(user_type
		(type_identifier))) @constructor

(anonymous_initializer
	("init")) @constructor

(parameter
	(simple_identifier) @parameter)

(parameter_with_optional_type
	(simple_identifier) @parameter)

; lambda parameters
(lambda_literal
	(lambda_parameters
		(variable_declaration
			(simple_identifier) @parameter)))

;;; Function calls

; function()
(call_expression
	. (simple_identifier)) @function

; object.function() or object.property.function()
(call_expression
	(navigation_expression
		(navigation_suffix
			(simple_identifier)) . )) @function