#include <array>
#include <mutex>
#include <thread>

#include <java-utils/java_symbols.hpp>

using namespace java_symbols;

static bool std_ends_with(const std::string& string, std::string_view suffix)
{
	return string.length() >= suffix.length() and suffix == std::string_view(string.c_str() + string.length() - suffix.length(), suffix.length());
}

int main(int argc, const char** argv)
{
	auto args = std_span<const char*>(argv + 1, argc - 1);
	
	auto parameter_dict = parse_arguments(args, {"-a", "--dry-run"});
	
	auto default_root = std::array<std::string, 1>({"."});
	
	auto fileroots = std_span<std::string>(default_root);
	
	const auto parameters = interpret_args(parameter_dict);
	
	if (auto it = parameter_dict.find(""); it != parameter_dict.end())
	{
		fileroots = it->second;
	}
	
	auto files = std::vector<std::filesystem::path>();
	files.reserve(256);
	
	for (const auto& fileroot : fileroots)
	{
		auto to_handle = std::filesystem::directory_entry(std::filesystem::path(fileroot));
		
		if (to_handle.is_regular_file())
		{
			files.emplace_back(std::move(to_handle));
		}
		else
		{
			for (auto& dir_entry : std::filesystem::recursive_directory_iterator(fileroot))
			{
				to_handle = std::move(dir_entry);
				
				if (to_handle.is_regular_file() and std_ends_with(to_handle.path().native(), ".java"))
				{
					files.emplace_back(std::move(to_handle));
				}
			}
		}
	}
	
	auto errors_mtx = std::mutex();
	auto errors = std::vector<std::string>();
	
	// auto threads = std::vector<std::jthread>(std::max(1u, std::thread::hardware_concurrency()));
	auto threads = std::vector<std::thread>(std::max(1u, std::thread::hardware_concurrency()));
	
	{
		auto begin = std::size_t(0);
		
		for (std::size_t i = 0; i != std::size(threads); ++i)
		{
			auto remainder = std::size(files) % std::size(threads);
			auto length = std::size(files) / std::size(threads) + bool(i < remainder);
			
			threads[i] = std::thread([&, begin, length]() noexcept -> void
			{
				for (auto j = begin; j != begin + length; ++j)
				{
					try
					{
						handle_file(std::move(files[j]), parameters);
					}
					catch (std::exception& ex)
					{
						auto lg = std::lock_guard(errors_mtx);
						errors.emplace_back(ex.what());
					}
				}
			});
			
			begin += length;
		}
	}
	
	for (auto& thread : threads)
	{
		thread.join();
	}
	
	threads.clear();
	
	if (not errors.empty())
	{
		auto message = std::string("Error: exceptions occured during the process:\n");
		
		for (const auto& error : errors)
		{
			message += "* ";
			message += error;
			message += "\n";
		}
		
		throw std::runtime_error(message);
	}
}
