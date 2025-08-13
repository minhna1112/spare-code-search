;;; Error node
(ERROR) @error.node

;;; Class definitions

;; Regular classes, data classes, sealed classes, abstract classes
(class_declaration
	(type_identifier) @class.name) @class.declaration

;; Object declarations (singletons)
(object_declaration
    (type_identifier) @object.name) @object.declaration

;; Companion objects
(class_body 
    (companion_object 
        (type_identifier)? @companion.name)  ; name is optional
    ) @companion.declaration


;; Interfaces
;;(interface_declaration
   ;; (type_identifier) @interface.name) @interface.declaration

;; Type aliases (can be used for class-like abstractions)
(type_alias
    (type_identifier) @type.alias.name) @type.alias.declaration

;;; Function definitions

(function_declaration
	. (simple_identifier) @function.name) @function.declaration

;;(getter
;;	("get")) @function.builtin.declaration
;;(setter
;;	("set")) @function.builtin.declaration

;;(primary_constructor) @constructor.declaration
;;(secondary_constructor
;;	("constructor")) @constructor.declaration

;;(constructor_invocation
;;	(user_type
;;		(type_identifier))) @constructor.declaration

(anonymous_initializer
	("init")) @constructor.declaration

;;(parameter
;;	(simple_identifier) @parameter.name) @parameter.declaration

;;(parameter_with_optional_type
;;	(simple_identifier) @parameter.name) @parameter.declaration

; lambda parameters
(lambda_literal
	(lambda_parameters
		(variable_declaration
			(simple_identifier) @parameter.name))) @parameter.declaration

;;; Function calls

; function()
(call_expression
	. (simple_identifier) @function.name) @function.declaration

; object.function() or object.property.function()
(call_expression
	(navigation_expression
		(navigation_suffix
			(simple_identifier) @function.name) . )) @function.declaration