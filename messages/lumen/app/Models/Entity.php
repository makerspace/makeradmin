<?php
namespace App\Models;

use DB;

/**
 * Entity class
 */
class Entity
{
	public $entity_id = null;     // The database unique id for the entity
	protected $data = [];         // Holds the data of the object
	protected $pagination = null; // No pagination by default
	protected $relations = [];    // An array with information about relations to other entities
	protected $type = null;       // The type of the entity, eg. "member"
	protected $join = null;       // Specify the relation table we should join, if any
	protected $columns = [
		"type" => [
			"column" => "entity.type",
			"select" => "entity.type",
		],
		"entity_id" => [
			"column" => "entity.entity_id",
			"select" => "entity.entity_id",
		],
		"created_at" => [
			"column" => "entity.created_at",
			"select" => "DATE_FORMAT(entity.created_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"updated_at" => [
			"column" => "entity.updated_at",
			"select" => "DATE_FORMAT(entity.updated_at, '%Y-%m-%dT%H:%i:%sZ')",
		],
		"title" => [
			"column" => "entity.title",
			"select" => "entity.title",
		],
		"description" => [
			"column" => "entity.description",
			"select" => "entity.description",
		],
	];
	protected $sort = ["created_at", "desc"]; // An array with sorting options eg. ["entity_id", "desc"] or [["date_updated", "asc"],["date_created","desc"]]
	protected $validation = [];               // Validation rules

	/**
	 * Constructor
	 */
	function __construct($entity_id = null)
	{
		$this->entity_id = $entity_id;
	}

	/**
	 * Do some preprocessing before we can start building our query:
	 *   1) Figure out if we need to join another table to get our result
	 *   2) Apply sorting
	 */
	protected function _preprocessFilters(&$filters)
	{
		if(is_array($filters))
		{
			foreach($filters as $id => $filter)
			{
				if($id == "type")
				{
					$this->type = $filter;
					// TODO: Should not be a hardcoded list
					if(in_array($this->type, ["accounting_transaction", "accounting_period", "accounting_instruction", "accounting_account", "member", "mail", "product", "rfid", "subscription", "invoice"]))
					{
						$this->join = $this->type;
					}

					// Remove the filter to prevent further processing
					unset($filters[$id]);
				}
				// Sorting
				else if("sort" == $id)
				{
					$this->sort = $filter;
					unset($filters[$id]);
				}
			}
		}
	}
	
	/**
	 * Build the base query with selecting entity types, tables, columns, join, sort and filtering removed items.
	 */
	protected function _buildLoadQuery($show_deleted = false)
	{
		// Get all entities
		$query = DB::table("entity");

		// Type
		if($this->type !== null)
		{
			$query = $query->where("entity.type", "=", $this->type);
		}

		// Join data table
		if($this->join !== null)
		{
			$query = $query->join($this->join, "{$this->join}.entity_id", "=", "entity.entity_id");
		}

		// Get columns
		foreach($this->columns as $name => $column)
		{
			$query = $query->selectRaw("{$column["select"]} AS `{$name}`");
		}

		// Show deleted entities or not?
		if($show_deleted === true)
		{
			// Include the deleted_at column in output only when we show deleted content
			$this->columns["deleted_at"] = [
				"column" => "entity.deleted_at",
				"select" => "entity.deleted_at",
			];
		}
		else
		{
			// The deleted_at should be null, which means it is not yet deleted
			$query = $query->whereNull("entity.deleted_at");
		}

		// Return the query
		return $query;
	}

	/**
	 * Apply standard filters like pagination, search and relation
	 * All unknown filters are treated like arbritrary WHERE key=value
	 */
	protected function _applyFilter($query, &$filters)
	{
		// Filter on entity_id
		if(!is_array($filters))
		{
			$query = $query->where("entity.entity_id", "=", $filters);
		}
		// Filter in arbitrary parameters
		else
		{
			// Go through filters
			foreach($filters as $id => $filter)
			{
				// Pagination
				if("per_page" == $id)
				{
					$this->pagination = $filter;
					unset($filters[$id]);
				}
				// Search filter
				else if("search" == $id)
				{
					// Check if there is a search function in the model
					if(method_exists($this, "_search"))
					{
						$this->_search($query, $filter);
					}
					unset($filters[$id]);
				}
				// Relations
				else if("relations" == $id)
				{
					foreach($filter as $relation)
					{
						// Load the related entity and get it's entity_id
						$entity = Entity::Load($relation);
						if(empty($entity))
						{
							throw new \Exception("Could not find entity: ".json_encode($relation));
							return false;
						}

						$entity_id = $entity->entity_id;

						// Get all relation to this entity
						$query2 = DB::table("relation")
							->whereRaw("{$entity_id} IN (entity1, entity2)")
							->get();

						// Filter out related entities
						$relatedEntities = null;
						foreach($query2 as $qw)
						{
							$relatedEntities[] = ($qw->entity1 == $entity_id ? $qw->entity2 : $qw->entity1);
						}

						$query = $query->whereIn("entity.entity_id", $relatedEntities);
					}
					unset($filters[$id]);
				}
				// Filter on arbritrary columns
				else
				{
					if(!is_array($filter))
					{
						$query = $query->where($id, "=", $filter);
					}
					else
					{
						$query = $query->where($id, $filter[0], $filter[1]);
					}
					unset($filters[$id]);
				}
			}
		}

		return $query;
	}

	public function _applySorting($query)
	{
		// Sort result
		if($this->sort !== null)
		{
			// Sort on multiple columns
			if(is_array($this->sort[0]))
			{
				foreach($this->sort as $s)
				{
					$query = $query->orderBy($this->columns[$s[0]]["column"], $s[1]);
				}
			}
			// Sort on single column
			else
			{
				// The column could be either an arbritary column like a SUM(meep) AS total, or a "real" column like entity.entity_id
				if(array_key_exists($this->sort[0], $this->columns))
				{
					$query = $query->orderBy($this->columns[$this->sort[0]]["column"], $this->sort[1]);
				}
				else
				{
					$query = $query->orderBy($this->sort[0], $this->sort[1]);
				}
			}
		}

		return $query;
	}

	/**
	 * Get a list of entities (called statically)
	 *
	 * Create an instance of the class and call the function non-static
	 */
	public static function list($filters = [])
	{
		return (new static())->_list($filters);
	}

	/**
	 * Same as above, but called non-statically
	 */
	protected function _list($filters = [])
	{
		// Preprocessing (join or type and sorting)
		$this->_preprocessFilters($filters);

		// Build base query
		$query = $this->_buildLoadQuery($filters);

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Sort
		$query = $this->_applySorting($query);

		// Paginate
		if($this->pagination != null)
		{
			$query->paginate($this->pagination);
		}

		// Run the MySQL query
		$data = $query->get();

		// Prepare array to be returned
		$result = [
			"data" => $data
		];

		// Pagination
		if($this->pagination != null)
		{
			$result["total"]     = $query->getCountForPagination();
			$result["per_page"]  = $this->pagination;
			$result["last_page"] = ceil($result["total"] / $result["per_page"]);
		}

		return $result;
	}

	/**
	 * Load an entity (called statically)
	 *
	 * Create an instance of the class and call the function non-static
	 */
	public static function load($filters, $show_deleted = false)
	{
		return (new static())->_load($filters, $show_deleted);
	}

	/**
	 * Same as above, but called non-statically
	 */
	protected function _load($filters, $show_deleted = false)
	{
		// Preprocessing (join or type and sorting)
		$this->_preprocessFilters($filters);

		// Build base query
		$query = $this->_buildLoadQuery();

		// Apply standard filters like entity_id, relations, etc
		$query = $this->_applyFilter($query, $filters);

		// Get data from database
		$data = (array)$query->first();

		// Return false if no entity was found in database
		if(empty($data))
		{
			return false;
		}
		
		// Create a new entity based on type
		// TODO: Should not be a hardcoded list
		$type = ($this->type !== null ? $this->type : $data["type"]);
		switch($type)
		{
			case "accounting_account":
				$entity = new AccountingAccount;
				break;

			case "accounting_instruction":
				$entity = new AccountingInstruction;
				break;

			case "accounting_transaction":
				$entity = new AccountingTransaction;
				break;

			case "group":
				$entity = new Group;
				break;

			case "invoice":
				$entity = new Invoice;
				break;

			case "mail":
				$entity = new Mail;
				break;

			case "member":
				$entity = new Member;
				break;

			case "product":
				$entity = new Product;
				break;

			case "rfid":
				$entity = new Rfid;
				break;

			case "subscription":
				$entity = new Subscription;
				break;

			default:
				$entity = new Entity;
		}

		// Populate the entity with data
		foreach($data as $key => $value)
		{
			$entity->{$key} = $value;
		}

		return $entity;
	}

	/**
	 * A helper function used in addRelation() and removeRelation()
	 */
	private function _loadRelation($relation)
	{
		if(is_numeric($relation))
		{
			return $relation;
		}

		// Load the specified entity
		$entity2 = Entity::load($relation);

		// Bail out on error
		if(empty($entity2))
		{
//			throw new Exception("Could not create relation: The entity you have specified could not be found");
			return false;
		}
		else
		{
			return $entity2->entity_id;
		}
	}

	/**
	 * Return an array of all relations
	 */
	public function getRelations()
	{
		$relations = [];

		foreach($this->relations as $relation)
		{
			$relations[] = $relation["entity_id"];
		}

		return $relations;
	}

	/**
	 * Add one single relation to another entity
	 */
	public function addRelation($relation)
	{
		if(!($entity_id = $this->_loadRelation($relation)))
		{
			return false;
		}

		// Make sure we don't get any duplicates in the relations
		if(!array_key_exists($entity_id, $this->relations))
		{
			// Add the relation
			$this->relations[$entity_id] = [
				"entity_id" => $entity_id,
				"action"    => "add",
			];
		}
	}

	/**
	 * Add an array of relations to other entities
	 */
	public function addRelations(array $relations)
	{
		foreach($relations as $relation)
		{
			$this->addRelation($relation);
		}
	}

	/**
	 * Removes an relation to another entity
	 */
	public function removeRelation($relation)
	{
		if(!($entity_id = $this->_loadRelation($relation)))
		{
			return false;
		}

		// Make sure the relation does exist
		if(!array_key_exists($entity_id, $this->relations))
		{
			// Removed the relation
			$this->relations[$entity_id]["action"] = "remove";
		}
	}

	/**
	 * Save the entity to database
	 *
	 * If there is no entity_id specified, a new entity is created
	 * If there is a entity_id specified, it is being updated
	 */
	public function save()
	{
		// Get the data to insert into the relation table
		$inserts = [];
		foreach($this->columns as $name => $data)
		{
			if(!strpos($data["column"], "."))
			{
				continue;
			}

			list($table, $column) = explode(".", $data["column"]);
			if($table == $this->join && array_key_exists($column, $this->data))
			{
				$inserts[$column] = $this->data[$column];
			}
		}

		// Update an existing entity
		if($this->entity_id !== null)
		{
			// Update a row in the entity table
			DB::table("entity")
				->where("entity_id", $this->entity_id)
				->update([
					"updated_at"  => date("c"),
					"title"       => $this->data["title"]       ?? null,
					"description" => $this->data["description"] ?? null,
				]);

			// Update a row in the relation table
			if(!empty($inserts))
			{
				DB::table($this->join)
					->where("entity_id", $this->entity_id)
					->update($inserts);
			}
		}
		// Create a new entity
		else
		{
			// Create a new row in the entity table
			$this->entity_id = DB::table("entity")->insertGetId([
				"type"        => $this->type,
				"title"       => $this->data["title"]       ?? null,
				"description" => $this->data["description"] ?? null,
				"created_at"  => date("c"),
				"updated_at"  => date("c"),
			]);

			// Create a row in the relation table
			if(!empty($inserts))
			{
				$inserts["entity_id"] = $this->entity_id;
				DB::table($this->join)->insert($inserts);
			}
		}

		// Go through the list of relations
		foreach($this->relations as &$relation)
		{
			// Only process relation that have been changed since the entity was loaded or created
			if($relation["action"])
			{
				if($relation["action"] == "add")
				{
					// Create the relation
					DB::table("relation")->insert([
						"entity1" => $this->entity_id,
						"entity2" => $relation["entity_id"]
					]);
				}
				else if($relation["action"] = "remove")
				{
					// TODO: Remove relation
/*
					DB::table("relation")->remove([
						"entity1" => $this->entity_id,
						"entity2" => $relation["entity_id"]
					]);
*/
				}
				unset($relation["action"]);
			}
		}

		return true;
	}

	/**
	 * Delete an entity
	 *
	 * A soft delete is used as standard and will only flag the entity as deleted
	 * To permanently delete an entity set $permanent = true
	 */
	public function delete($permanent = false)
	{
		// Check that we have a id provided
		if($this->entity_id === null)
		{
			return false;
		}

		// TODO: Delete relations and data in joins

		if($permanent === true)
		{
			// Permanent delete
			DB::table("entity")
				->where("entity_id", $this->entity_id)
				->delete();
		}
		else
		{
			// Soft delete
			DB::table("entity")
				->where("entity_id", $this->entity_id)
				->update(["deleted_at" => date("c")]);
		}

		return true;
	}

	/**
	 * Get a property
	 */
	public function __get($name)
	{
		if(array_key_exists($name, $this->data))
		{
			return $this->data[$name];
		}

		$trace = debug_backtrace();
		trigger_error(
			'Undefined property via __get(): ' . $name .
			' in ' . $trace[0]['file'] .
			' on line ' . $trace[0]['line'],
			E_USER_NOTICE);
		return null;
	}

	/**
	 * Set a property
	 */
	public function __set($name, $value)
	{
		$this->data[$name] = $value;
	}

	/**
	 * Check if a property is set
	 */
	public function __isset($name)
	{
		return isset($this->data[$name]);
	}

	/**
	 * Convert the data on an entity into an array
	 */
	public function toArray()
	{
		$x = $this->data;
		$x["entity_id"] = $this->entity_id;
		return $x;
	}

	/**
	 * Validate the data based on the filters in $this->validation
	 */
	public function validate()
	{
		// Go through the filters
		foreach($this->validation as $field => $rules)
		{
			// Do not apply a filter if there is not data to validate
			if(!array_key_exists($field, $this->data))
			{
				continue;
			}

			// Each field can have multiple rules
			foreach($rules as $rule)
			{
				// The value is required to be not empty
				if($rule == "required")
				{
					if(empty($this->data[$field]))
					{
						throw new EntityValidationException($field, "The value can not be empty");
					}
				}
				// The value should be unique in database (except from deleted entities)
				else if($rule == "unique")
				{
					// Check if there is anything in the database
					$result = Entity::load([
						"type" => $this->join,
						$field => $this->data[$field]
					]);

					// A unique value collision is not fatal if it is from the same entity thas is being validated (itself)... or else we could not save an entity
					if(!empty($result) && ($result->entity_id != $this->entity_id))
					{
						throw new EntityValidationException($field, "The value needs to be unique in the database");
					}
				}
				// Validate a date according to ISO8601 standard
				else if($rule == "date")
				{
					// TODO
				}
				// E-mail
				else if($rule == "email")
				{
					// TODO
				}
				// Personnummer
				else if($rule == "civicregno")
				{
					// TODO
				}
				// Phone number
				else if($rule == "phone")
				{
					// TODO
				}
				else
				{
					throw new EntityValidationException($field, "Unknown validation rule {$rule}");
				}
			}
		}
	}
}

/**
 * Thrown when a Entity::validate() fails and catched in app/Exceptions/Handler.php to return a standardized validation error result
 */
class EntityValidationException extends \Exception
{
	protected $column;

	function __construct($column, $message)
	{
		$this->column = $column;
		$this->message = $message;
	}

	function getColumn()
	{
		return $this->column;
	}
}